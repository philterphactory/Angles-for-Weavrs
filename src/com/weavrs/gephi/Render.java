package com.weavrs.gephi;

import java.awt.Color;
import java.io.File;
import java.io.IOException;
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
import org.gephi.layout.plugin.force.StepDisplacement;
import org.gephi.layout.plugin.force.yifanHu.YifanHuLayout;
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
import org.gephi.partition.api.PartitionController;
import org.gephi.partition.plugin.NodeColorTransformer;
import org.gephi.statistics.plugin.Modularity;
import org.openide.util.Lookup;

public class Render {
  public static void main(String[] args) throws Exception {
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

    YifanHuLayout layout = new YifanHuLayout(null, new StepDisplacement(1f));
    layout.setGraphModel(graphModel);
    layout.resetPropertiesValues();
    layout.setOptimalDistance(200f);

    layout.initAlgo();
    for (int i = 0; i < 100 && layout.canAlgo(); i++) {
      layout.goAlgo();
    }

    //Get Centrality
    GraphDistance distance = new GraphDistance();
    distance.setDirected(true);
    distance.execute(graphModel, attributeModel);


    //Run modularity algorithm - community detection
    Modularity modularity = new Modularity();
    modularity.execute(graphModel, attributeModel);

    //Partition with 'modularity_class', just created by Modularity algorithm
    PartitionController partitionController = Lookup.getDefault().lookup(PartitionController.class);
    AttributeColumn modColumn = attributeModel.getNodeTable().getColumn(Modularity.MODULARITY_CLASS);
    Partition p2 = partitionController.buildPartition(modColumn, graph);
    System.out.println(p2.getPartsCount() + " partitions found");
    NodeColorTransformer nodeColorTransformer2 = new NodeColorTransformer();
    nodeColorTransformer2.randomizeColors(p2);
    partitionController.transform(p2, nodeColorTransformer2);


    //Rank size by centrality
    AttributeColumn centralityColumn = attributeModel.getNodeTable().getColumn(GraphDistance.BETWEENNESS);
    Ranking centralityRanking = rankingController.getModel().getRanking(Ranking.NODE_ELEMENT, centralityColumn.getId());
    AbstractSizeTransformer sizeTransformer = (AbstractSizeTransformer) rankingController.getModel().getTransformer(Ranking.NODE_ELEMENT, Transformer.RENDERABLE_SIZE);
    sizeTransformer.setMinSize(3);
    sizeTransformer.setMaxSize(10);
    rankingController.transform(centralityRanking,sizeTransformer);

    //Preview
    model.getProperties().putValue(PreviewProperty.SHOW_NODE_LABELS, Boolean.TRUE);
    model.getProperties().putValue(PreviewProperty.EDGE_COLOR, new EdgeColor(Color.GRAY));
    model.getProperties().putValue(PreviewProperty.EDGE_THICKNESS, new Float(0.1f));
    model.getProperties().putValue(PreviewProperty.NODE_LABEL_FONT, model.getProperties().getFontValue(PreviewProperty.NODE_LABEL_FONT).deriveFont(8));

    //Export
    ExportController ec = Lookup.getDefault().lookup(ExportController.class);
    try {
      //ec.exportFile(new File("headless_simple.png"));
      PNGExporter pngExporter = (PNGExporter) ec.getExporter("png");
      pngExporter.setWorkspace(workspace);
      pngExporter.setWidth(512);
      pngExporter.setHeight(512);
      pngExporter.setTransparentBackground(false);
      pngExporter.setMargin(50);
      ec.exportFile(new File("output/out.png"), pngExporter);
    } catch (IOException ex) {
      ex.printStackTrace();
      return;
    }
  }
}
