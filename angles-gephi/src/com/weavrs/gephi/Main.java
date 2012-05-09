package com.weavrs.gephi;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.*;
import java.net.*;

public class Main {
  public static void main(String[] args) throws Exception {
    ObjectMapper mapper = new ObjectMapper();
    for(String filename : args) {
      try {
        URL url;
        File file = new File(filename);
        if(file.exists()) {
          url = file.toURI().toURL();
        } else {
          url = new URL(filename);
        }
        Render render = new YifanByDegreeRender();
        render.setConfig(mapper.readTree(url));
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
