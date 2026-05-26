var TRI_FILL   = "rgba(100, 160, 255, 0.22)";
var TRI_STROKE = "rgba(100, 160, 255, 0.55)";
var TET_FILL   = "rgba(255, 140, 80,  0.18)";
var TET_STROKE = "rgba(255, 140, 80,  0.50)";

var triangles = __TRI_JSON__;
var tetras    = __TET_JSON__;

function attachOverlay() {
  if (typeof network === "undefined") { setTimeout(attachOverlay, 100); return; }

  var container = document.getElementById("mynetwork");
  var visCanvas = container.querySelector("canvas");
  if (!visCanvas) { setTimeout(attachOverlay, 100); return; }

  var oc = document.createElement("canvas");
  oc.style.position      = "absolute";
  oc.style.top           = "0"; oc.style.left = "0";
  oc.style.pointerEvents = "none";
  oc.style.zIndex        = "5";
  container.style.position = "relative";
  container.appendChild(oc);

  var ctx = oc.getContext("2d");

  function syncSize() {
    oc.width  = visCanvas.width;
    oc.height = visCanvas.height;
  }
  syncSize();

  function getNodePos(id) {
    var pos = network.getPositions([id]);
    if (!pos[id]) return null;
    return network.canvasToDOM({ x: pos[id].x, y: pos[id].y });
  }

  function drawPolygon(ids, fill, stroke) {
    var pts = ids.map(getNodePos);
    if (pts.some(p => p === null)) return;
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
    ctx.closePath();
    ctx.fillStyle   = fill;   ctx.fill();
    ctx.strokeStyle = stroke; ctx.lineWidth = 1.2; ctx.stroke();
  }

  function tetFaces(ids) {
    return [
      [ids[0], ids[1], ids[2]],
      [ids[0], ids[1], ids[3]],
      [ids[0], ids[2], ids[3]],
      [ids[1], ids[2], ids[3]],
    ];
  }

  function redraw() {
    syncSize();
    ctx.clearRect(0, 0, oc.width, oc.height);
    tetras.forEach(function(ids) {
      tetFaces(ids).forEach(function(face) { drawPolygon(face, TET_FILL, TET_STROKE); });
    });
    triangles.forEach(function(ids) { drawPolygon(ids, TRI_FILL, TRI_STROKE); });
  }

  network.on("afterDrawing", function() { redraw(); });
  window.addEventListener("resize", function() { syncSize(); redraw(); });
  redraw();
}

setTimeout(attachOverlay, 50);
