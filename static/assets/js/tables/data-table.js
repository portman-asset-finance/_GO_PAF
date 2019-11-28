"use strict";
+function($, window){

	var dataTables = {};

	dataTables.init = function() {
		$('#dt-opt').DataTable({
			"ordering": false,
        	"info":     false,
			"searching": false

		});
	};	
	window.dataTables = dataTables;

}(jQuery, window);

// initialize app
+function($) {
	dataTables.init();		
}(jQuery);
