package com.weavrs.gephi;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.*;
import java.net.*;

public class Main {
  public static void main(String[] args) throws Exception {
    ObjectMapper mapper = new ObjectMapper();
    for(String filename : args) {
      try {
        File file = new File(filename);
        Render render = new YifanByDegreeRender();
        render.setConfig(mapper.readTree(file));
        long started = System.currentTimeMillis();
        render.render();
        System.out.format("%s rendered in %dms.\n", filename, System.currentTimeMillis() - started);
      } catch(Exception e) {
        System.out.format("Exception processing %s:\n\n", filename);
        e.printStackTrace();
      }
    }
  }
}
