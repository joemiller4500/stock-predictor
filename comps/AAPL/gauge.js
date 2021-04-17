data = d3.csv("prediction1.csv").then(function(data){
    // return data[0];
    var max, min, last, curr, i;

    console.log(data[0])
    val = function(data,i){
        return data[i];
    };
    var value = val(data,0);
    max = +value.Open;
    min = +value.Open;
    for (i=1; i<data.length; i++){
        value = val(data,i);
        // console.log(value);
        value = +value.Open
        // console.log(value);
        if (value > max){
            max = value;
        };
        if (value < min){
            min = value;
        };
    };
    last = val(data, (data.length - 2));
    last = +last.Open;
    console.log(last);
    curr = val(data, (data.length-1));
    // console.log(curr);
    curr = +curr.Open;
    console.log(curr);
    var stepa = (min + ((max-min)/3));
    var stepb = min + 2*(max-min)/3;
    console.log(stepa + stepb + curr + min + max + last)
    

    var trace = [{
        domain: { x: [0, 1], y: [0, 1] },
        value: curr,
        delta: { reference: last },
        title: {text: "Current Actual Price"},
        type: "indicator",
        mode: "gauge+number+delta",
        gauge: {
        axis: { range: [min, max]},
        bar: { color: "lightgreen"},
        borderwidth: 3,
        bordercolor: "black",
        steps: [
            { range: [min, stepa], color: "red" },
            { range: [stepa, stepb], color: 'yellow'},
            { range: [stepb, max], color: 'green'}
        ]
        }
    }];
        

    var layout = {
        paper_bgcolor: 'white'
    };
    Plotly.newPlot("gauge", trace, layout);
});