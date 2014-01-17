$('#button-go').on('click', function(e){
	var lang, data, $log;
	e.preventDefault();
	lang = $('#lang-select').val();
	data = JSON.parse($('#attached-wikis').text());
	$log = $('#logging');
	$.each(data.wikis, function(index, value){
		$.ajax({
			url: location.protocol + '//tools.wmflabs.org/globalprefs/api/',
			dataType: 'json',
			async: false,
			data: {'wiki': value, 'value': lang},
			success: function(data) {
				$log.append('Set value on ' + value);
			}
		});
	});
});
