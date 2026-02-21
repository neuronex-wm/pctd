let s = null;

let mdata;

function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

function getUrlParam(parameter, defaultvalue){
    var urlparameter = defaultvalue;
    if(window.location.href.indexOf(parameter) > -1){
        urlparameter = getUrlVars()[parameter];
        }
    return urlparameter;
}

function switchSwcFile(e) {
	s.unloadNeuron('foo', null, swc);	
	var e = document
    .getElementById("loadCell");
 const f = e.options[e.selectedIndex].value;
  if (f) {
	const r = jQuery.get(f).done(function(data) {
		/*alert( "Data Loaded: " + data );*/
		const  swc = sharkViewer.swcParser(data);
		if (Object.keys(swc).length > 0) {
        s.loadNeuron('foo',null, swc);
        s.render();
      } else {
        alert("Please upload a valid swc file.");}
	
	
	});
	/*const r = new FileReader();*/
    /*r.onload = (e2) => {
      const swcTxt = e2.target.result;
      const  swc = sharkViewer.swcParser(swcTxt);
      if (Object.keys(swc).length > 0) {
        s.loadNeuron('foo', '#ff0000', swc);
        s.render();
      } else {
        alert("Please upload a valid swc file.");
      }
    };
    r.readAsText(f);*/
	/*const  swc = sharkViewer.swcParser(swcTxt);*/

  } else {
    alert("Failed to load file");
  }
};


window.onload = function() {
document
    .getElementById("loadCell")
    .addEventListener("change", switchSwcFile, false);	
  var swc = sharkViewer.swcParser(document.getElementById("swc").text);
	
  var cellvars = getUrlParam('cell', 'M3.JS.B5.C11.swc')
  cellvars = 'swc/' + cellvars
  document.getElementById("loadCell").value = cellvars;
  mdata = JSON.parse(document.getElementById("metadata_swc").text);
  s = new sharkViewer.default({
    animated: false,
    mode: 'particle',
    dom_element: document.getElementById('container'),
    metadata: mdata,
    showAxes: 10000,
    //cameraChangeCallback: (data) => { console.log(data) }
  });
  window.s = s;
  const r = jQuery.get(cellvars).done(function(data) {
		/*alert( "Data Loaded: " + data );*/
	    swc = sharkViewer.swcParser(data);
		if (Object.keys(swc).length > 0) {
        s.loadNeuron('foo',null, swc);
        s.render();
      } else {
        alert("Please upload a valid swc file.");}
  });
  s.init();
  s.animate();
  const swc2 = sharkViewer.swcParser(document.getElementById("swc2").text);
  // s.loadNeuron('swc2', '#ff0000', swc2);
  s.loadNeuron('swc', null, swc);
  s.render();
	
};
