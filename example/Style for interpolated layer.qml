<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" maxScale="0" version="3.0.2-Girona" minScale="1e+8">
  <pipe>
    <rasterrenderer band="1" classificationMax="27.3995" classificationMin="17.6011" alphaBand="-1" opacity="1" type="singlebandpseudocolor">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>MinMax</limits>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader classificationMode="2" clip="0" colorRampType="INTERPOLATED">
          <colorramp name="[source]" type="gradient">
            <prop v="gradient" k="rampType"/>
            <prop v="0.13;222,235,247,255:0.26;198,219,239,255:0.39;158,202,225,255:0.52;107,174,214,255:0.65;66,146,198,255:0.78;33,113,181,255:0.9;8,81,156,255" k="stops"/>
            <prop v="247,251,255,255" k="color1"/>
            <prop v="8,48,107,255" k="color2"/>
            <prop v="0" k="discrete"/>
          </colorramp>
          <item alpha="255" label="22.5" color="#73b3d8" value="22.5003"/>
          <item alpha="255" label="24.9" color="#2879b9" value="24.9499"/>
          <item alpha="255" label="27.4" color="#08306b" value="27.3995"/>
          <item alpha="255" label="17.6" color="#f7fbff" value="17.6011"/>
          <item alpha="255" label="20.1" color="#c8ddf0" value="20.0507"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeRed="255" colorizeGreen="128" colorizeStrength="100" saturation="0" grayscaleMode="0" colorizeOn="0" colorizeBlue="128"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
