using System.Text.Json.Serialization;

namespace FactoryCutPlanner.Models;

public class RectangularDuctSpec
{
    [JsonPropertyName("width_mm")]
    public decimal WidthMm { get; set; }

    [JsonPropertyName("height_mm")]
    public decimal HeightMm { get; set; }

    [JsonPropertyName("length_mm")]
    public decimal LengthMm { get; set; }

    [JsonPropertyName("thickness_mm")]
    public decimal ThicknessMm { get; set; }

    [JsonPropertyName("insulation_enabled")]
    public bool InsulationEnabled { get; set; }
}

public class AHUSpec
{
    [JsonPropertyName("width_mm")]
    public decimal WidthMm { get; set; }

    [JsonPropertyName("height_mm")]
    public decimal HeightMm { get; set; }

    [JsonPropertyName("length_mm")]
    public decimal LengthMm { get; set; }

    [JsonPropertyName("panel_thickness_mm")]
    public decimal PanelThicknessMm { get; set; }

    [JsonPropertyName("has_profile_framework")]
    public bool HasProfileFramework { get; set; }
}

public class FittingSpec
{
    [JsonPropertyName("main_dimension_mm")]
    public decimal MainDimensionMm { get; set; }

    [JsonPropertyName("thickness_mm")]
    public decimal ThicknessMm { get; set; }
}
