package com.weavrs.gephi;

import java.awt.Color;
import java.awt.Font;
import java.io.*;
import java.util.*;
import org.gephi.data.attributes.api.*;
import org.gephi.filters.api.*;
import org.gephi.filters.plugin.graph.*;
import org.gephi.filters.spi.*;
import org.gephi.graph.api.*;
import org.gephi.io.exporter.api.*;
import org.gephi.io.exporter.preview.*;
import org.gephi.io.importer.api.*;
import org.gephi.io.processor.plugin.*;
import org.gephi.layout.plugin.force.*;
import org.gephi.layout.plugin.force.yifanHu.*;
import org.gephi.layout.plugin.forceAtlas2.*;
import org.gephi.layout.plugin.labelAdjust.*;
import org.gephi.partition.api.*;
import org.gephi.partition.plugin.*;
import org.gephi.preview.api.*;
import org.gephi.preview.types.*;
import org.gephi.project.api.*;
import org.gephi.ranking.api.*;
import org.gephi.ranking.plugin.transformer.*;
import org.gephi.statistics.plugin.*;
import org.openide.util.Lookup;
import com.fasterxml.jackson.databind.*;

public class YifanByDegreeRender implements Render {
  private Config config;

  public void setConfig(JsonNode config) throws IOException {
    this.config = new Config(config);
  }

  public void render() throws ConfigException,IOException {
    if(this.config == null) {
      throw new ConfigException("Not configured! Please call setConfig() first.");
    }
    ProjectController pc = Lookup.getDefault().lookup(ProjectController.class);
    pc.newProject();
    Workspace workspace = pc.getCurrentWorkspace();

    //Get models and controllers for this new workspace - will be useful later
    AttributeModel attributeModel = Lookup.getDefault().lookup(AttributeController.class).getModel();
    GraphModel graphModel = Lookup.getDefault().lookup(GraphController.class).getModel();
    PreviewModel model = Lookup.getDefault().lookup(PreviewController.class).getModel();
    ImportController importController = Lookup.getDefault().lookup(ImportController.class);
    FilterController filterController = Lookup.getDefault().lookup(FilterController.class);
    RankingController rankingController = Lookup.getDefault().lookup(RankingController.class);

    //Import file       
    Container container;
    container = importController.importFile(this.config.getInputFile());

    importController.process(container, new DefaultProcessor(), workspace);

    //See if graph is well imported
    Graph graph = graphModel.getGraph();

    // Filter graph by k-Core (default k=9)
    if(this.config.shouldFilterByKcore()) {
      KCoreBuilder builder = Lookup.getDefault().lookup(KCoreBuilder.class);
      KCoreBuilder.KCoreFilter kCoreFilter = (KCoreBuilder.KCoreFilter) builder.getFilter();
      kCoreFilter.setK(this.config.getKcoreK());
      Query kcoreQuery = filterController.createQuery(kCoreFilter);

      // Check the filter worked
      GraphView view = filterController.filter(kcoreQuery);
      graphModel.setVisibleView(view);

      graph = graphModel.getGraphVisible();
      System.out.println("kcore Filtered Nodes: " + graph.getNodeCount());
      System.out.println("kcore Filtered Edges: " + graph.getEdgeCount());
    }

    // Rank size by Degree
    Ranking degreeRanking = rankingController.getModel().getRanking(Ranking.NODE_ELEMENT, Ranking.DEGREE_RANKING);
    AbstractSizeTransformer sizeTransformer = (AbstractSizeTransformer) rankingController.getModel().getTransformer(Ranking.NODE_ELEMENT, Transformer.RENDERABLE_SIZE);
    sizeTransformer.setMinSize(100);
    sizeTransformer.setMaxSize(500);
    rankingController.transform(degreeRanking,sizeTransformer);

    // Rank color by Degree
    AbstractColorTransformer colorTransformer = (AbstractColorTransformer) rankingController.getModel().getTransformer(Ranking.NODE_ELEMENT, Transformer.RENDERABLE_COLOR);
    if(this.config.hasColourloversPalette()) {
      colorTransformer.setColors(this.config.getColourloversColors());
      colorTransformer.setColorPositions(this.config.getColourloversPositions());
    } else {
      colorTransformer.setColors(new Color[]{new Color(0x2C7BB6), new Color(0xFFFFBF), new Color(0xD7191C)});
      colorTransformer.setColorPositions(new float[] { 0.0f, 0.5f, 1.0f });
    }

    //Interpolator interpolator = Interpolator.newBezierInterpolator(0.1f, 0.95f, 0.0f, 1.0f);
    //Interpolator interpolator = Interpolator.newBezierInterpolator(0.0f, 1.0f, 0.1f, 0.95f);
    Interpolator interpolator = Interpolator.newBezierInterpolator(0.2f, 0.95f, 1.0f, 1.0f);
    rankingController.setInterpolator(interpolator);
    rankingController.transform(degreeRanking,colorTransformer);

    YifanHuLayout layout = new YifanHuProportional().buildLayout();
    layout.setGraphModel(graphModel);
    layout.resetPropertiesValues();

    layout.initAlgo();
    layout.setOptimalDistance(2000f);
    layout.setInitialStep(400f);
    layout.setStep(400f);
    int i = 0;
    for (; i < 500 && layout.canAlgo(); i++) {
      layout.goAlgo();
    }
    System.out.format("Yifan Hu layout iterated %d times.\n", i);

    // Preview properties
    if(!this.config.backgroundTransparent()) {
      model.getProperties().putValue(PreviewProperty.BACKGROUND_COLOR, this.config.getColour("background"));
    }

    model.getProperties().putValue(PreviewProperty.EDGE_OPACITY, new Float(this.config.getOpacity("edge")));
    model.getProperties().putValue(PreviewProperty.EDGE_THICKNESS, new Float(this.config.getThickness("edge")));

    model.getProperties().putValue(PreviewProperty.SHOW_NODE_LABELS, Boolean.TRUE);
    model.getProperties().putValue(PreviewProperty.NODE_LABEL_COLOR, new DependantOriginalColor(DependantOriginalColor.Mode.PARENT));
    model.getProperties().putValue(PreviewProperty.NODE_LABEL_FONT, this.config.getFont());
    model.getProperties().putValue(PreviewProperty.NODE_LABEL_OUTLINE_COLOR, new DependantColor(this.config.getColour("outline")));
    model.getProperties().putValue(PreviewProperty.NODE_LABEL_OUTLINE_OPACITY, new Float(this.config.getOpacity("outline")));
    model.getProperties().putValue(PreviewProperty.NODE_LABEL_OUTLINE_SIZE, new Float(this.config.getThickness("outline")));

    model.getProperties().putValue(PreviewProperty.NODE_OPACITY, new Float(this.config.getOpacity("node")));
    
    //Export
    ExportController ec = Lookup.getDefault().lookup(ExportController.class);
    try {
      PNGExporter pngExporter = (PNGExporter) ec.getExporter("png");
      pngExporter.setWorkspace(workspace);
      pngExporter.setWidth(this.config.getWidth());
      pngExporter.setHeight(this.config.getHeight());
      pngExporter.setTransparentBackground(this.config.backgroundTransparent());
      ec.exportFile(this.config.getOutputFile(), pngExporter);
    } catch (IOException ex) {
      ex.printStackTrace();
      return;
    }
  }
}
