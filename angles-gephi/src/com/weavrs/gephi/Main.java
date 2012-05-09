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
        Render render = new Render(mapper.readTree(url));
        render.render();
      } catch(Exception e) {
        System.out.format("Exception processing %s:\n\n", filename);
        e.printStackTrace();
      }
    }
  }
}
