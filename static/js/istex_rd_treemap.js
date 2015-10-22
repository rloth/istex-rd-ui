// ----------------------------------------------
// original: http://bl.ocks.org/mbostock/4063582
// ----------------------------------------------
// package istex_rd::vizout
// ------------------------

var rd = {
  version: "0.1"
};

// do_treemap
// ----------
// Appel : do_treemap(900, 500, "data/corpora.tree.json", "p.ici")
//           arg1  --  largeur
//           arg2  --  hauteur
//           arg3  --  données treejson
//                     {"name":"els", "children":[{"name":"truc","size":42},...]
//                     (par ex: flare.json ou sortie -o tree de sampler.py)
//           arg4  --  selecteur de l'élément à décorer

rd.do_treemap = function (W, H, my_data_path, my_anchor_elt) {

  // DIMS
  var margin = {top: 40, right: 70, bottom: 40, left: 70},
      width = W - margin.left - margin.right,
      height = H - margin.top - margin.bottom;

  // COLORS
  //~ var color = d3.scale.category20c();  // avec sous-degrades
  var color = d3.scale.category20();   // avec couleurs light
  //~ var color = d3.scale.category10();

  var treemap = d3.layout.treemap()
      .size([width, height])
      .sticky(true)
      .mode("squarify")
      .value(function(d) { return d.size; }) ;

  var div = d3.select(my_anchor_elt).append("div")
      .style("position", "relative")
      .style("width", (width + margin.left + margin.right) + "px")
      .style("height", (height + margin.top + margin.bottom) + "px")
      .style("left", margin.left + "px")
      .style("top", margin.top + "px");

  d3.json(my_data_path, function(error, root) {
    if (error) throw error;

    var node = div.datum(root).selectAll(".node")
        .data(treemap.nodes)
      .enter()
        .append("div")
        .attr("class", function(d) { return d.children ? "node nonterm" : "node terminal"; } )
        //~ 
        .style("background", function(d) { return d.children ? color(d.name) : null; })
        //~ .sort(function(a,b) {return b.name > a.name;})
        .call(position) ;

    node.append("text")
        .text(function(d) { return d.name; })
        //~ .style("font-size", rel_size) // ne marche pas pour petites quantités => normaliser ?
        // line-height same as div height for vertical align effect
        .style("line-height", function(d) { return d.children ? d.dy *.8 + "px" : rel_size; }) ;
        
  });
}

// position globale
function position() {
      this.style("left", function(d) { return d.x + "px"; })
          .style("top", function(d) { return d.y + "px"; })
          .style("width", function(d) { return Math.max(0, d.dx - 1) + "px"; })
          .style("height", function(d) { return Math.max(0, d.dy - 1) + "px"; });
      // console.log(this.style("left")) ;
      // console.log(this.style("top")) ;
      // console.log(this.style("width")) ;
      // console.log(this.style("height")) ;
}

function rel_size(d) { 
  var fsize = 0 ;
  // console.log(d) ;
  if (d.children) {
    fsize = Math.sqrt(d.value) * 0.5
  }
  else {
    fsize = 20
  }
  return fsize + "px"; }