package com.weavrs.gephi;

import java.io.*;
import com.fasterxml.jackson.databind.*;

public interface Render {
  public void render() throws ConfigException,IOException;
  public void setConfig(JsonNode config) throws IOException;
}
