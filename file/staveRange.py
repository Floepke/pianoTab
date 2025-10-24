from pydantic import BaseModel, Field

class StaveRange(BaseModel):
    """
    Defines the key range for a stave in a particular line of music.
    The index of the StaveRange corresponds to the stave index it applies to.
    If both lowestKey and highestKey are 0, the range is determined by the music content.
    """
    lowestKey: int = Field(default=0, ge=0, le=88, description="Lowest key (1-88), 0 means auto-determined by music")
    highestKey: int = Field(default=0, ge=0, le=88, description="Highest key (1-88), 0 means auto-determined by music")
    
    class Config:
        extra = 'forbid'
