package com.weavrs.gephi;

import com.fasterxml.jackson.databind.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.awt.Font;
import java.awt.Color;

public class Config {
  JsonNode config;
  public Config(JsonNode config) {
    this.config = config;
  }

  public File getInputFile() throws ConfigException {
    if(this.config.path("input").isValueNode()) {
      return new File(this.config.path("input").asText());
    } else {
      throw new ConfigException("input filename not found.");
    }
  }

  public File getOutputFile() throws ConfigException {
    if(this.config.path("output").isValueNode()) {
      return new File(this.config.path("output").asText());
    } else {
      throw new ConfigException("output filename not found.");
    }
  }

  public Font getFont() throws ConfigException {
    JsonNode font = this.config.path("font");
    if(font.path("name").isTextual() && 
       font.path("size").isInt()) {
      return new Font(font.path("name").asText(), Font.PLAIN, font.path("size").asInt());
    } else {
      return new Font("Arial", Font.PLAIN, 12);
    }
  }

  public boolean shouldFilterByKcore() throws ConfigException {
    JsonNode kcore = this.config.path("kcoreFilter");
    if(kcore.isBoolean()) {
      return kcore.asBoolean();
    }
    if(kcore.isMissingNode() || kcore.isObject()) {
      return true;
    }
    throw new ConfigException("kcoreFilter should be a boolean or a hash.");
  }

  public float getOpacity(String name) throws ConfigException {
    JsonNode opacity = this.config.path("opacity");
    if(!opacity.isObject()) {
      throw new ConfigException("opacity should be a hash.");
    }
    if(opacity.path(name).isNumber()) {
      return (float)opacity.path(name).asDouble();
    } else {
      return 100.0f;
    }
  }
  public Color getColour(String name) throws ConfigException {
    JsonNode colour = this.config.path("colour");
    if(!colour.isObject()) {
      throw new ConfigException("colour should be a hash.");
    }
    if(colour.path(name).isTextual()) {
      return Color.decode("0x" + colour.path(name).asText());
    } else {
      return Color.black;
    }
  }

  public JsonNode getColourloversPalette(int id) throws IOException {
    String url = String.format("http://www.colourlovers.com/api/palette/%d?showPaletteWidths=1&format=json", id);
    return new ObjectMapper().readTree(new URL(url)).path(0);
  }

  public boolean hasColourloversPalette() {
    return this.config.path("colourloversPalette").isValueNode();
  }

  public Color[] getColourloversColors() throws IOException {
    int id = this.config.path("colourloversPalette").asInt();
    JsonNode palette = this.getColourloversPalette(id);
    Color[] colors = new Color[palette.path("colors").size()];
    int i = 0;
    for(JsonNode rgb : palette.path("colors")) {
      colors[i] = Color.decode("0x" + rgb.asText());
      i += 1;
    }
    return colors;
  }

  public float[] getColourloversPositions() throws IOException {
    int id = this.config.path("colourloversPalette").asInt();
    JsonNode palette = this.getColourloversPalette(id);
    float[] positions = new float[palette.path("colorWidths").size()];
    int i = 0;
    double pos = 0;
    for(JsonNode width : palette.path("colorWidths")) {
      pos += width.asDouble();
      positions[i] = (float)pos;
      i += 1;
    }
    return positions;
  }

  public int getKcoreK() throws ConfigException {
    if(this.config.path("kcoreFilter").path("k").isInt()) {
      return this.config.path("kcoreFilter").path("k").asInt();
    }
    return 9;
  }
}
