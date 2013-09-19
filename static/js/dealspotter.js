

// SVG parameters
var w = 600;
var h = 320;
var padding = 65;
var top_padding = 15;
var carScale = 0.34;
var path;
var goodColor = '#5AC9E9';
var badColor = '#dddddd';
var carWidth = 40;
var carHeight = 40;

// Initial slider values
var lo = 5000;
var hi = 17000;

// Other variables
var url_root = 'http://sfbay.craigslist.org';
var data;
var unfiltered_data;

// Puts commas in numbers
function comma_separate_number(val){
  while (/(\d+)(\d{3})/.test(val.toString())){
    val = val.toString().replace(/(\d+)(\d{3})/, '$1'+','+'$2');
  }
  return val;
}

// Returns number string with 'k' shorthand for 1000
function kstyle_number(val){
  return Math.round(val/1000) + "K";
}

// Returns sign string of number
function sign_char(val) {
  return val < 0 ? "-" : "";
}



$.getJSON('data', function(d) {
  unfiltered_data = d.items;
  d3.xml("static/img/car_new.svg", "image/svg+xml", function(xml) {

    // Car SVG
    var importedNode = document.importNode(xml.documentElement, true);


    //Create X scale
    var xScale = d3.scale.linear()
                .domain([1995, 2014])
                .range([padding, w - padding]);
    //Create Y scale
    var yScale = d3.scale.linear()
                .domain([0, 220000])
                .range([h - padding, top_padding]);

    //Define X axis
    var xAxis = d3.svg.axis()
                      .scale(xScale)
                      .orient("bottom")
                      .ticks(5)
                      .tickFormat(d3.format(".0f"));
    //Define Y axis
    var yAxis = d3.svg.axis()
                      .scale(yScale)
                      .orient("left")
                      .ticks(5)
                      .tickFormat(function(d) { return d/1000+"K"; });
    //Create SVG element
    var svg = d3.select("#graph-container")
                      .append("svg")
                      .attr("width", w)
                      .attr("height", h)
                      .attr("class", "center");
    //Create X axis
    svg.append("g")
       .attr("class", "axis")
       .attr("transform", "translate(0," + (h - padding) + ")")
       .call(xAxis);

    //Create Y axis
    svg.append("g")
       .attr("class", "axis")
       .attr("transform", "translate(" + padding + "," + 0 + ")")
       .call(yAxis);

    //Create X label
    svg.append("text")
      .attr("class", "axis_label")
      .attr("text-anchor", "middle")
      .attr("x", (w)/2)
      .attr("y", h - padding + 40)
      .text("Year");

    //Create Y label
    svg.append("text")
      .attr("class", "axis_label")
      .attr("text-anchor", "middle")
      .attr("x", -130)
      .attr("y", 10)
      .attr("transform", "rotate(-90)")
      .text("Miles");

    // Shows the original craigslist ad in a modal
    function show_ad(title, body, url, price) {
        $('#AdModal .modal-title').html("$" + comma_separate_number(price) + ": " + title);
        $('#AdModal .modal-body').html(body);
        $('#AdModal .modal-footer').html("<a target=\"_blank\" href = \"" + url_root + url + "\">See on Craigslist</a>");
        $('#AdModal').modal('show');
    }


    // Called whenever uses a slider or picks a new model
    function update_display()
    {

      // Filter unfiltered_data to user price and model constraints
      data = [];
      filt_count = 0;
      for (var i = unfiltered_data.length-1; i >= 0; i--) {
        if (unfiltered_data[i].model == model && unfiltered_data[i].price >= lo && unfiltered_data[i].price <= hi){
          data[filt_count++] = unfiltered_data[i];
        }
      }

      //Remove all cars so that z-order remains correct
      svg.selectAll(".car_subcontainer").remove();

      //Create car svg variable
      var cl = svg.selectAll(".car_subcontainer")
        .data(data, function(d) {
          return d.url;
        });


      cl.enter()
        .append("g")
        .on("click", function (d, i) {
          show_ad(d.title, d.body, d.url, d.price);
        })
        .attr("class", "car_subcontainer")
        .each(function (d, i) {
          var car = this.appendChild(importedNode.cloneNode(true));
          if (d.delta>1000) {
            fill = goodColor;
          }
          else{
            fill = badColor;
          }

          $($(car).children()[3].children).attr("fill", fill);
        });

      cl.exit().remove();

      cl
        .attr("transform", function(d, i){
          return "translate(" + (xScale(d.year) - carWidth/2) + ","
          + (yScale(d.miles) - carHeight/2) + ")"
          + " scale(" + carScale + ")";
        })
        .transition().style("opacity");


      // Show tooltip upon hover over car
      $('.car_subcontainer').tipsy({
        gravity: 'w',
        html: true,
        title: function() {
          return "$" + Math.round(this.__data__.price/100)/10 + "K";}
      });


      // Repopulate table with rows
      $( "#table_body" ).html("");
      var textToInsert = [];
      for (var i = data.length-1; i >= 0; i--) {
        var c = 0;
        if (data[i].delta>0){
          savings_class = 'pos_savings';
        }
        else {
          savings_class = 'neg_savings';
        }

        textToInsert[c++] = "<tr idx=" + i + ">";
        textToInsert[c++] = "<td>" + (data.length-i) + "</td>";
        textToInsert[c++] = "<td>" + data[i].year + "</td>";
        textToInsert[c++] = "<td>" + kstyle_number(data[i].miles) + "</td>";
        textToInsert[c++] = "<td>" + "$" + comma_separate_number(data[i].price) + "</td>";
        textToInsert[c++] = "<td class=" + savings_class + ">" + sign_char(data[i].delta) + "$" + comma_separate_number(Math.abs(Math.round(data[i].delta))) + "</td>";
        textToInsert[c++] = "</tr>";
        $( "#table_body" ).append(textToInsert.join(''));
      }


      // Make table rows clickable
      $('.table > tbody > tr').click(function() {
        idx = $(this).attr("idx");
        show_ad(data[idx].title, data[idx].body, data[idx].url, data[idx].price);
      });


      // Change mouse appearace when user hovers over rows.
      $('.table > tbody > tr').mouseenter(function() {
        $(this).removeClass("row-unhover").addClass("row-hover");
      });


      // Change mouse appearace when user stops hovering over rows.
      $('.table > tbody > tr').mouseleave(function() {
        $(this).removeClass("row-hover").addClass("row-unhover");
      });

    } //update


    // Tab for user to select "list" or "graph" mode
    $('.container-toggler').click(function(){
      $('.container-toggle').hide();
      $($(this).attr('data-container-id')).show();
    });


    // Car model dropdown on regular page
    $('.model').click(function(){
      model = $(this).attr('value');
      $('#dropdown_title').html($(this).html());
      update_display();
    });

    // Car model dropdown on the introductory modal
    $('.splash-model').click(function(){
      model = $(this).attr('value');
      $('#ModelModal').modal('hide');
      $('#dropdown_title').html($(this).html());
      $('#list').click();
      update_display();
    });

    // Price slider control
    $( "#slider-range" ).slider({
      range: true,
      min: 0,
      max: 25000,
      step: 500,
      values: [ lo, hi ],
      slide: function( event, ui ) {
        lo = ui.values[0];
        hi = ui.values[1];
        $( "#amount" ).html( "$" + lo + " - " + "$" + hi);
        update_display();
      }
    });

    // Update price text above slider
    $( "#amount" ).html( "$" + $( "#slider-range" ).slider( "values", 0 ) + " - " +
      "$" + $( "#slider-range" ).slider( "values", 1 ) );

    // Slider style
    $( ".ui-slider-handle.ui-state-focus" ).css("background-color", "#aaa");
    $( ".ui-slider-handle.ui-state-focus" ).css("color", "#aaa");
    $( ".ui-slider-handle.ui-state-focus" ).css("background", "#aaa");


  }); //d3.xml

}); //getJson

// Show introductory modal when user arrives
$(window).load(function(){
    $('#ModelModal').modal('show');
});
