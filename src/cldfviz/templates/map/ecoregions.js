{
    onEachFeature: function(feature, layer) {
        layer.bindTooltip(feature.properties.ECO_NAME, {});
    },
    style: function(feature) {
        switch (feature.properties.BIOME | 0) {
            case 1: return {fillColor: '#42791B', weight: 1, opacity: 0.8, fillOpacity: 0.7};
            case 2: return {fillColor: '#D5AC00', weight: 1, opacity: 0.8, fillOpacity: 0.7};
            case 3: return {fillColor: '#7AFD1D'};
            case 4: return {fillColor: '#72C934', weight: 1, opacity: 0.8, fillOpacity: 0.7};
            case 5: return {fillColor: '#005400', weight: 1, opacity: 0.8, fillOpacity: 0.7};
            case 6: return {fillColor: '#28A15A', weight: 1, opacity: 0.8, fillOpacity: 0.7};
            case 7: return {fillColor: '#FFDE54', weight: 1, opacity: 0.8, fillOpacity: 0.7};
            case 8: return {fillColor: '#CEDF88', weight: 1, opacity: 0.8, fillOpacity: 0.7};
            case 9: return {fillColor: '#81B5FF', weight: 1, opacity: 0.8, fillOpacity: 0.7, tooltip: feature.properties.ECO_NAME};
            case 10: return {fillColor: '#C7B1EA', weight: 1, opacity: 0.8, fillOpacity: 0.7, tooltip: feature.properties.ECO_NAME};
            case 11: return {fillColor: '#88DFCE', weight: 1, opacity: 0.8, fillOpacity: 0.7, tooltip: feature.properties.ECO_NAME};
            case 12: return {fillColor: '#C97234', weight: 1, opacity: 0.8, fillOpacity: 0.7, tooltip: feature.properties.ECO_NAME};
            case 13: return {fillColor: '#FFF6D6', weight: 1, opacity: 0.8, fillOpacity: 0.7, tooltip: feature.properties.ECO_NAME};
            case 14: return {fillColor: '#E146C3', weight: 1, opacity: 0.8, fillOpacity: 0.7, tooltip: feature.properties.ECO_NAME};
            case 98: return {fillColor: '#FFFFFF', weight: 1, opacity: 0.5, fillOpacity: 0.4, tooltip: feature.properties.ECO_NAME};
            case 99: return {fillColor: '#FFFFFF', weight: 1, opacity: 0.5, fillOpacity: 0.4, tooltip: feature.properties.ECO_NAME};
        }
    }
}
