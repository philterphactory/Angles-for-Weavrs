package com.weavrs.gephi;

import java.awt.Color;
import java.awt.Font;
import java.io.File;
import java.io.IOException;
import java.util.*;
import org.gephi.data.attributes.api.AttributeColumn;
import org.gephi.data.attributes.api.AttributeController;
import org.gephi.data.attributes.api.AttributeModel;
import org.gephi.filters.api.FilterController;
import org.gephi.filters.api.Query;
import org.gephi.filters.api.Range;
import org.gephi.filters.plugin.graph.DegreeRangeBuilder.DegreeRangeFilter;
import org.gephi.graph.api.DirectedGraph;
import org.gephi.graph.api.GraphController;
import org.gephi.graph.api.GraphModel;
import org.gephi.graph.api.GraphView;
import org.gephi.graph.api.UndirectedGraph;
import org.gephi.io.exporter.api.ExportController;
import org.gephi.io.exporter.preview.PNGExporter;
import org.gephi.io.importer.api.Container;
import org.gephi.io.importer.api.EdgeDefault;
import org.gephi.io.importer.api.ImportController;
import org.gephi.io.processor.plugin.DefaultProcessor;
import org.gephi.layout.plugin.labelAdjust.LabelAdjust;
import org.gephi.layout.plugin.force.StepDisplacement;
import org.gephi.layout.plugin.force.yifanHu.YifanHuLayout;
import org.gephi.layout.plugin.forceAtlas2.*;
import org.gephi.preview.api.PreviewController;
import org.gephi.preview.api.PreviewModel;
import org.gephi.preview.api.PreviewProperty;
import org.gephi.preview.types.EdgeColor;
import org.gephi.project.api.ProjectController;
import org.gephi.project.api.Workspace;
import org.gephi.ranking.api.Ranking;
import org.gephi.ranking.api.RankingController;
import org.gephi.ranking.api.Transformer;
import org.gephi.ranking.plugin.transformer.AbstractColorTransformer;
import org.gephi.ranking.plugin.transformer.AbstractSizeTransformer;
import org.gephi.statistics.plugin.GraphDistance;
import org.gephi.partition.api.Partition;
import org.gephi.partition.api.Part;
import org.gephi.partition.api.PartitionController;
import org.gephi.partition.plugin.NodeColorTransformer;
import org.gephi.statistics.plugin.Modularity;
import org.openide.util.Lookup;

public class Render {
  public static void main(String[] args) throws Exception {
    render();
  }

  public static void benchmark() throws Exception {
    System.out.println("Warming up...");
    int runs = 10;
    for(int i = 0; i < runs; i++) {
      render();
    }
    System.out.println("Benchmarking...");
    long times[] = new long[runs];
    for(int i = 0; i < runs; i++) {
      long t = System.currentTimeMillis();
      render();
      times[i] = System.currentTimeMillis() - t;
    }
    float avg = 0;
    for(int i = 0; i < runs; i++) {
      avg += times[i];
    }
    avg /= runs;
    System.out.format("%d runs took %f milliseconds per run.\n", runs, avg);
  }

  public static void render() throws Exception {
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
    File file = new File("data/percival-keywords-2012-05-07-16-21-34.gexf");
    container = importController.importFile(file);
    container.getLoader().setEdgeDefault(EdgeDefault.UNDIRECTED);

    importController.process(container, new DefaultProcessor(), workspace);

    //See if graph is well imported
    DirectedGraph graph = graphModel.getDirectedGraph();
    System.out.println("Nodes: " + graph.getNodeCount());
    System.out.println("Edges: " + graph.getEdgeCount());

    //Filter      
    DegreeRangeFilter degreeFilter = new DegreeRangeFilter();
    degreeFilter.init(graph);
    degreeFilter.setRange(new Range(30, Integer.MAX_VALUE));     //Remove nodes with degree < 30
    Query query = filterController.createQuery(degreeFilter);
    GraphView view = filterController.filter(query);
    graphModel.setVisibleView(view);    //Set the filter result as the visible view

    ForceAtlas2 fa2Layout = new ForceAtlas2(new ForceAtlas2Builder());
    fa2Layout.setGraphModel(graphModel);
    fa2Layout.resetPropertiesValues();
    fa2Layout.initAlgo();
    fa2Layout.setEdgeWeightInfluence(1.0);
    fa2Layout.setGravity(1.0);
    fa2Layout.setAdjustSizes(false);
    fa2Layout.setScalingRatio(5.0);
    fa2Layout.setBarnesHutTheta(1.2);
    fa2Layout.setJitterTolerance(0.1);

    for (int i = 0; i < 150 && fa2Layout.canAlgo(); i++) {
      fa2Layout.goAlgo();
    }

    LabelAdjust adjustLayout = new LabelAdjust(null);
    adjustLayout.setGraphModel(graphModel);
    adjustLayout.initAlgo();
    adjustLayout.setSpeed(0.5);
    adjustLayout.setAdjustBySize(false);
    for (int i = 0; i < 50000 && adjustLayout.canAlgo(); i++) {
      adjustLayout.goAlgo();
    }

    //Get Centrality
    GraphDistance distance = new GraphDistance();
    distance.setDirected(true);
    distance.execute(graphModel, attributeModel);

    /*
    //Run modularity algorithm - community detection
    Modularity modularity = new Modularity();
    modularity.execute(graphModel, attributeModel);

    //Partition with 'modularity_class', just created by Modularity algorithm
    PartitionController partitionController = Lookup.getDefault().lookup(PartitionController.class);
    AttributeColumn modColumn = attributeModel.getNodeTable().getColumn(Modularity.MODULARITY_CLASS);
    Partition p2 = partitionController.buildPartition(modColumn, graph);
    System.out.println(p2.getPartsCount() + " partitions found");
    NodeColorTransformer nodeColorTransformer2 = new NodeColorTransformer();
    Color[] colors = new Color[] {
      new Color(0,160,176),
      new Color(106,74,60),
      new Color(204,51,63),
      new Color(235,104,65),
      new Color(237,201,81)
    };
    int i = 0;
    for(Part p : p2.getParts()) {
      System.out.format("Partition %s = %s\n", p, colors[i]);
      nodeColorTransformer2.getMap().put(p.getValue(), colors[i]);
      i += 1;
    }
    partitionController.transform(p2, nodeColorTransformer2);
    */

    //Rank size by centrality
    AttributeColumn centralityColumn = attributeModel.getNodeTable().getColumn(GraphDistance.BETWEENNESS);
    Ranking centralityRanking = rankingController.getModel().getRanking(Ranking.NODE_ELEMENT, centralityColumn.getId());
    AbstractSizeTransformer sizeTransformer = (AbstractSizeTransformer) rankingController.getModel().getTransformer(Ranking.NODE_ELEMENT, Transformer.RENDERABLE_SIZE);
    sizeTransformer.setMinSize(3);
    sizeTransformer.setMaxSize(10);
    rankingController.transform(centralityRanking,sizeTransformer);

    AbstractColorTransformer colorTransformer = (AbstractColorTransformer) rankingController.getModel().getTransformer(Ranking.NODE_ELEMENT, Transformer.RENDERABLE_COLOR);
    colorTransformer.setColors(new Color[] {
      Color.decode("0xFE4365"),
      Color.decode("0xFC9D9A"),
      Color.decode("0xF9CDAD"),
      Color.decode("0xC8C8A9"),
      Color.decode("0x83AF9B")
    });
    colorTransformer.setColorPositions(new float[] { 0.23f, 0.30f, 0.36f, 0.43f, 1.0f });
    rankingController.transform(centralityRanking,colorTransformer);

    //Preview
    model.getProperties().putValue(PreviewProperty.SHOW_NODE_LABELS, Boolean.TRUE);
    model.getProperties().putValue(PreviewProperty.EDGE_COLOR, new EdgeColor(EdgeColor.Mode.SOURCE));
    model.getProperties().putValue(PreviewProperty.EDGE_RESCALE_WEIGHT, Boolean.TRUE);
    model.getProperties().putValue(PreviewProperty.EDGE_THICKNESS, new Float(0.8f));
    model.getProperties().putValue(PreviewProperty.NODE_BORDER_WIDTH, new Float(0.0f));
    model.getProperties().putValue(PreviewProperty.NODE_LABEL_FONT, new Font("Ostrich Sans Rounded", Font.PLAIN, 12));

    //Export
    ExportController ec = Lookup.getDefault().lookup(ExportController.class);
    try {
      //ec.exportFile(new File("headless_simple.png"));
      PNGExporter pngExporter = (PNGExporter) ec.getExporter("png");
      pngExporter.setWorkspace(workspace);
      pngExporter.setWidth(768);
      pngExporter.setHeight(768);
      pngExporter.setTransparentBackground(false);
      pngExporter.setMargin(50);
      ec.exportFile(new File("output/out.png"), pngExporter);
    } catch (IOException ex) {
      ex.printStackTrace();
      return;
    }
  }
}
