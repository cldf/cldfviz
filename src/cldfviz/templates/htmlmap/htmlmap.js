var geojson = $geojson;
var markers = [],
    combinations = $combinations,
    flayers = {},
    map = L.map('map', {fullscreenControl: true}).setView([5, 160], 2);

var OpenStreetMap_BlackAndWhite = L.tileLayer('http://{s}.tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
});
OpenStreetMap_BlackAndWhite.addTo(map);

function onEachFeature(feature, layer) {
    var fid = feature.properties.family_id,
        html = "<h3>" + feature.properties.name + "</h3><dl>";
    html += '<p>' + feature.properties.values + '</p>';
    layer.bindPopup(html);
    if (flayers.hasOwnProperty(feature.properties.values)) {
        flayers[feature.properties.values].push(layer);
    } else {
        flayers[feature.properties.values] = [layer];
    }
    layer.bindTooltip(feature.properties.name);
    markers.push(layer);
}
L.geoJSON([geojson], {
    onEachFeature: onEachFeature,
    pointToLayer: function (feature, latlng) {
        return L.marker(latlng, {icon: L.icon({iconUrl: feature.properties.icon, iconSize: [15, 15]})})
    }
}).addTo(map);

var group = new L.featureGroup(markers);
map.fitBounds(group.getBounds());

var flayer, combination, overlays = {};

for (var i = 0; i < combinations.length; i++) {
    combination = combinations[i];
    flayer = L.layerGroup(flayers[combination[0]]);
    flayer.addTo(map);
    overlays[combination[0] + ' (' + combination[1] + ')'] = flayer
}
L.control.layers({}, overlays).addTo(map);
