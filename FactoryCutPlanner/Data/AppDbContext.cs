using FactoryCutPlanner.Models;
using Microsoft.EntityFrameworkCore;

namespace FactoryCutPlanner.Data;

/// <summary>
/// EF Core database context — the single gateway to the SQLite database.
///
/// WHY a constructor parameter for dbPath:
///   - Development: points to "../hvac_factory_ops.db" (relative to project)
///   - Testing: can use ":memory:" for fast in-memory SQLite tests
///   - Production: absolute path next to the packaged .exe
///   Hardcoding the path would break in at least two of these scenarios.
///
/// WHY OnModelCreating is so detailed:
///   The scaffolder generated column mappings (e.g., HasColumnName("product_id"))
///   because SQLite uses snake_case and C# uses PascalCase. Without these mappings,
///   EF Core would look for columns named "ProductId" instead of "product_id" → crash.
/// </summary>
public partial class AppDbContext : DbContext
{
    private readonly string _dbPath;

    /// <summary>
    /// Creates a new context pointing to the given SQLite database file.
    /// </summary>
    /// <param name="dbPath">
    /// Path to the SQLite .db file. Examples:
    ///   "../hvac_factory_ops.db" (development)
    ///   ":memory:" (unit tests)
    ///   "/Users/.../hvac_factory_ops.db" (production)
    /// </param>
    public AppDbContext(string dbPath)
    {
        _dbPath = dbPath;
    }

    /// <summary>
    /// Parameterless constructor for EF Core tooling (migrations, scaffold).
    /// Falls back to a sensible default path for development.
    /// </summary>
    public AppDbContext()
    {
        var baseDir = System.AppContext.BaseDirectory;
        _dbPath = System.IO.Path.Combine(baseDir, "hvac_factory_ops.db");
    }

    // ----- DbSet properties -----
    // Each DbSet represents one table. EF Core uses these to build queries.

    public virtual DbSet<BomItem> BomItems { get; set; }
    public virtual DbSet<Product> Products { get; set; }
    public virtual DbSet<WorkOrder> WorkOrders { get; set; }
    public virtual DbSet<WorkOrderLine> WorkOrderLines { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        if (!optionsBuilder.IsConfigured)
        {
            optionsBuilder.UseSqlite($"Data Source={_dbPath}");
        }
    }

    /// <summary>
    /// Configures the EF Core model to match the existing SQLite schema exactly.
    ///
    /// WHY all these HasColumnName() calls:
    ///   SQLite uses snake_case (product_id), C# uses PascalCase (ProductId).
    ///   Without explicit mapping, EF Core would generate SQL like
    ///   "SELECT ProductId FROM bom_items" — which would fail because the
    ///   actual column is called "product_id".
    ///
    /// WHY ValueGeneratedOnAdd() instead of ValueGeneratedNever():
    ///   The scaffold generated ValueGeneratedNever() because SQLite doesn't
    ///   explicitly declare AUTOINCREMENT. But SQLite's INTEGER PRIMARY KEY
    ///   auto-assigns IDs by default (it's implicit). ValueGeneratedOnAdd()
    ///   tells EF Core "let the database assign the ID" — which is what we want
    ///   when inserting new records.
    ///
    /// WHY HasConversion&lt;double&gt;() on decimal properties:
    ///   SQLite stores all numbers as IEEE 754 doubles internally.
    ///   Our C# model uses decimal for precision, but we need EF Core to
    ///   know how to convert between SQLite's double and C#'s decimal.
    ///   The HasConversion&lt;double&gt;() call adds this bridging logic.
    /// </summary>
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // ──────────────────────────────────────────────
        // BOM ITEMS table configuration
        // ──────────────────────────────────────────────
        modelBuilder.Entity<BomItem>(entity =>
        {
            entity.ToTable("bom_items");

            entity.HasIndex(e => e.Id, "ix_bom_items_id");

            // WHY ValueGeneratedOnAdd: SQLite auto-assigns INTEGER PRIMARY KEY
            entity.Property(e => e.Id)
                .ValueGeneratedOnAdd()
                .HasColumnName("id");

            // WHY HasConversion<double>: SQLite stores FLOAT as double;
            // we convert to decimal in C# for exact arithmetic
            entity.Property(e => e.CostPerUnit)
                .HasConversion<double?>()
                .HasColumnType("FLOAT")
                .HasColumnName("cost_per_unit");

            entity.Property(e => e.QuantityPerUnit)
                .HasConversion<double>()
                .HasColumnType("FLOAT")
                .HasColumnName("quantity_per_unit");

            entity.Property(e => e.CreatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("created_at");

            entity.Property(e => e.Name)
                .HasColumnType("VARCHAR(255)")
                .HasColumnName("name");

            entity.Property(e => e.ProductId)
                .HasColumnName("product_id");

            entity.Property(e => e.Unit)
                .HasColumnType("VARCHAR(64)")
                .HasColumnName("unit");

            entity.Property(e => e.UpdatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("updated_at");

            // Relationship: BomItem → Product (many-to-one)
            // WHY CASCADE: deleting a product should delete its BOM items
            // (matches Python: cascade="all, delete-orphan")
            entity.HasOne(d => d.Product)
                .WithMany(p => p.BomItems)
                .HasForeignKey(d => d.ProductId);
        });

        // ──────────────────────────────────────────────
        // PRODUCTS table configuration
        // ──────────────────────────────────────────────
        modelBuilder.Entity<Product>(entity =>
        {
            entity.ToTable("products");

            entity.HasIndex(e => e.Id, "ix_products_id");

            entity.Property(e => e.Id)
                .ValueGeneratedOnAdd()
                .HasColumnName("id");

            // WHY JsonDictionaryConverter: the "attributes" column stores
            // polymorphic JSON (different keys for different product types).
            // This converter handles serialization/deserialization.
            entity.Property(e => e.Attributes)
                .HasConversion(new JsonDictionaryConverter())
                .HasColumnType("JSON")
                .HasColumnName("attributes");

            entity.Property(e => e.CreatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("created_at");

            entity.Property(e => e.Description)
                .HasColumnType("VARCHAR(1024)")
                .HasColumnName("description");

            entity.Property(e => e.Name)
                .HasColumnType("VARCHAR(255)")
                .HasColumnName("name");

            entity.Property(e => e.ProductType)
                .HasColumnType("VARCHAR(64)")
                .HasColumnName("product_type");

            entity.Property(e => e.UpdatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("updated_at");
        });

        // ──────────────────────────────────────────────
        // WORK ORDERS table configuration
        // ──────────────────────────────────────────────
        modelBuilder.Entity<WorkOrder>(entity =>
        {
            entity.ToTable("work_orders");

            entity.HasIndex(e => e.Id, "ix_work_orders_id");

            entity.Property(e => e.Id)
                .ValueGeneratedOnAdd()
                .HasColumnName("id");

            entity.Property(e => e.CreatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("created_at");

            entity.Property(e => e.ProductId)
                .HasColumnName("product_id");

            entity.Property(e => e.ProjectName)
                .HasColumnType("VARCHAR(255)")
                .HasColumnName("project_name");

            entity.Property(e => e.Quantity)
                .HasColumnName("quantity");

            entity.Property(e => e.UpdatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("updated_at");

            // WHY HasConversion<double?>: same as BomItem — SQLite stores
            // waste_factor as FLOAT (double), we want decimal in C#
            entity.Property(e => e.WasteFactor)
                .HasConversion<double?>()
                .HasDefaultValueSql("'0'")
                .HasColumnType("FLOAT")
                .HasColumnName("waste_factor");

            // Legacy relationship: WorkOrder → Product (many-to-one, nullable)
            // WHY CASCADE: matches the Python schema's ON DELETE CASCADE
            entity.HasOne(d => d.Product)
                .WithMany(p => p.WorkOrders)
                .HasForeignKey(d => d.ProductId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // ──────────────────────────────────────────────
        // WORK ORDER LINES table configuration
        // ──────────────────────────────────────────────
        modelBuilder.Entity<WorkOrderLine>(entity =>
        {
            entity.ToTable("work_order_lines");

            entity.HasIndex(e => e.Id, "ix_work_order_lines_id");

            entity.Property(e => e.Id)
                .ValueGeneratedOnAdd()
                .HasColumnName("id");

            entity.Property(e => e.CreatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("created_at");

            entity.Property(e => e.ProductId)
                .HasColumnName("product_id");

            entity.Property(e => e.Quantity)
                .HasColumnName("quantity");

            entity.Property(e => e.UpdatedAt)
                .HasDefaultValueSql("CURRENT_TIMESTAMP")
                .HasColumnType("DATETIME")
                .HasColumnName("updated_at");

            entity.Property(e => e.WorkOrderId)
                .HasColumnName("work_order_id");

            // WHY RESTRICT: prevents deleting a product that's being used
            // in an active work order. This is intentional — Python has the
            // same constraint: ForeignKey("products.id", ondelete="RESTRICT")
            entity.HasOne(d => d.Product)
                .WithMany(p => p.WorkOrderLines)
                .HasForeignKey(d => d.ProductId)
                .OnDelete(DeleteBehavior.Restrict);

            // WHY CASCADE (default): deleting a work order should delete its lines.
            // This matches Python: cascade="all, delete-orphan"
            // Note: .Lines (not .WorkOrderLines) — we renamed this in WorkOrder.cs
            entity.HasOne(d => d.WorkOrder)
                .WithMany(p => p.Lines)
                .HasForeignKey(d => d.WorkOrderId);
        });

        OnModelCreatingPartial(modelBuilder);
    }

    partial void OnModelCreatingPartial(ModelBuilder modelBuilder);
}
