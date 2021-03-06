/*
 * File: app/view/BMapPanel.js
 * Date: Fri May 04 2012 17:20:08 GMT+0800 (CST)
 *
 * This file was generated by Sencha Architect version 2.0.0.
 * http://www.sencha.com/products/architect/
 *
 * This file requires use of the Ext JS 4.0.x library, under independent license.
 * License of Sencha Architect does not include license for Ext JS 4.0.x. For more
 * details see http://www.sencha.com/license or contact license@sencha.com.
 *
 * This file will be auto-generated each and everytime you save your project.
 *
 * Do NOT hand edit this file.
 */

Ext.define('MyApp.view.BMapPanel', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.bmappanel',

    autoShow: true,
    height: 663,
    width: 628,
    title: 'My Panel',
    mapType: 'BMAP_NORMAL_MAP',
    city: '上海市',

    initComponent: function() {
        var me = this;

        Ext.applyIf(me, {
            mapControls: [
                'NavigationControl',
                'MapTypeControl',
                'ScaleControl'
            ]
        });

        me.callParent(arguments);
    },

    afterRender: function() {
        var point;

        this.callParent();     

        this.bmap = new BMap.Map(this.body.dom);

        if (typeof this.addControl == 'object' ) {
            this.bmap.addControl(this.addControl);
        }

        if (typeof this.setCenter === 'object') {
            if (typeof this.setCenter.geoCodeAddr === 'string'){
                this.geoCodeLookup(this.setCenter.geoCodeAddr);
            }else{
                point = new BMap.Point(this.setCenter.lng,this.setCenter.lat);
                this.bmap.centerAndZoom(point, this.zoomLevel);    

                if (typeof this.setCenter.marker === 'object' && typeof point === 'object'){
                    this.addMarker(point,this.setCenter.marker,this.setCenter.marker.clear);
                }
            }

        }
        else{
            this.bmap.centerAndZoom(this.city);
        }
        var self = this;
        this.bmap.addEventListener('tilesloaded', function(){
            self.onMapReady();

        });
    },

    onMapReady: function() {
        this.addMarkers(this.markers);
        this.addMapControls();
        this.addOptions();
    },

    getMap: function() {
        return this.bmap;
    },

    getCenter: function() {
        return this.getMap().getCenter();
    },

    addMarkers: function(markers) {
        if (Ext.isArray(markers)){
            for (var i = 0; i < markers.length; i++) {
                var mkr_point = new BMap.Point(markers[i].lng,markers[i].lat);
                this.addMarker(mkr_point,markers[i].marker,false,markers[i].setCenter, markers[i].listeners);
            }
        }
    },

    addMarker: function(point, marker, clear, center, listeners) {
        var evt;


        if (clear === true){
            this.getMap().clearOverlays();
        }
        if (center === true) {
            this.getMap().centerAndZoom(point, this.zoomLevel);
        }

        var mark = new BMap.Marker(point,marker);
        if (typeof listeners === 'object'){
            for (evt in listeners) {
                if (!listeners.hasOwnProperty(evt)) {
                    continue;
                }
                mark.addEventListener(evt, listeners[evt]);
            }
        }
        this.getMap().addOverlay(mark);

    },

    addMapControls: function() {
        if (this.mapType) {
            if (Ext.isArray(this.mapControls)) {
                for(var i=0;i<this.mapControls.length;i++){
                    this.addMapControl(this.mapControls[i]);
                }
            }else if(typeof this.mapControls === 'string'){
                this.addMapControl(this.mapControls);
            }else if(typeof this.mapControls === 'object'){
                this.getMap().addControl(this.mapControls);
            }
        }
    },

    addMapControl: function(mc) {
        var mcf = BMap[mc];
        if (typeof mcf === 'function') {
            this.getMap().addControl(new mcf());
        }    
    },

    addOptions: function() {
        if (Ext.isArray(this.mapConfOpts)) {
            var mc;
            for(i=0;i<this.mapConfOpts.length;i++){
                this.addOption(this.mapConfOpts[i]);
            }
        }else if(typeof this.mapConfOpts === 'string'){
            this.addOption(this.mapConfOpts);
        }        
    },

    addOption: function(mc) {
        var mcf = this.getMap()[mc];
        if (typeof mcf === 'function') {
            this.getMap()[mc]();
        }    
    },

    geoCodeLookup: function(addr) {
        this.geocoder = new BMap.Geocoder();
        this.geocoder.getPoint(addr, Ext.Function.bind(this.addAddressToMap, this), this.city);
    },

    addAddressToMap: function(point) {
        if (point){
            if (typeof this.setCenter.marker === 'object' && typeof point === 'object'){
                this.addMarker(point,this.setCenter.marker,this.setCenter.marker.clear,true, this.setCenter.listeners);
            }

        }
    }

});
