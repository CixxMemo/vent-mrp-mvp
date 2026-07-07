using System.Collections.Generic;
using System.Text.Json;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace FactoryCutPlanner.Data;

/// <summary>
/// Converts between a Dictionary&lt;string, JsonElement&gt; (used in C# code)
/// and a JSON string (stored in the SQLite "attributes" column).
///
/// WHY this exists:
/// The "products.attributes" column stores different JSON schemas depending
/// on product_type (RECTANGULAR_DUCT, AHU_CABINET, FITTING_DUCT).
/// EF Core has no built-in way to read/write arbitrary JSON from SQLite,
/// so we provide this explicit converter.
///
/// WHY Dictionary&lt;string, JsonElement&gt; instead of a strongly-typed class:
/// Because each product_type has a different set of keys. A single class
/// cannot represent all three. We parse into typed specs in the service layer.
/// </summary>
public class JsonDictionaryConverter : ValueConverter<Dictionary<string, JsonElement>, string>
{
    public JsonDictionaryConverter() : base(
        // C# → Database: serialize the dictionary to a JSON string
        dict => JsonSerializer.Serialize(dict, (JsonSerializerOptions?)null),
        // Database → C#: deserialize the JSON string back to a dictionary
        json => JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json, (JsonSerializerOptions?)null)
               ?? new Dictionary<string, JsonElement>()
    )
    { }
}
