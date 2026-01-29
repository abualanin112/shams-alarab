class WatermarkProcessor:
    """Handles logic for watermark overlay."""

    def __init__(self, position: str = "bottom-right", opacity: float = 1.0):
        self.position = position
        self.opacity = opacity

    def get_filter(self, stream_in: str, logo_input_index: int, stream_out: str) -> str:
        """
        Generate overlay filter.
        Standardized Visuals:
        - Scale: 4.5% of video height
        - Opacity: 0.75
        - Position: Bottom-Right with 20px margin
        """
        # Define coordinates based on position
        if self.position == "top-right":
            coords = "W-w-20:20"
        elif self.position == "bottom-right":
            coords = "W-w-20:H-h-20"
        elif self.position == "bottom-left":
            coords = "20:H-h-20"
        else:
            coords = "W-w-20:H-h-20"  # Default to bottom-right 20px

        logo_scale_label = f"[logo_scaled_{stream_out.strip('[]')}]"
        logo_label = f"[logo_proc_{stream_out.strip('[]')}]"

        # 1. Scale to 3.5% height (Refined Educational Standard)
        scale_filter = f"[{logo_input_index}:v]scale=-1:ih*0.035{logo_scale_label}"
        
        # 2. Opacity
        opacity_filter = f"{logo_scale_label}format=rgba,colorchannelmixer=aa={self.opacity}{logo_label}"
        
        # 3. Overlay
        overlay_filter = f"{stream_in}{logo_label}overlay={coords}{stream_out}"
        
        return f"{scale_filter};{opacity_filter};{overlay_filter}"
