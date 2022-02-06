(function() {
    var req_url = "https://pfgl-psaly.cloud.okteto.net/api/v1/standings";
    $.ajax({
        dataType: "json",
        url: req_url,
        success: function(data) {
            var standings_html = '<div class="table-row is--header"><div class="table-column"><h4 class="table-column-info is--header">Rank</h4></div><div class="table-column"><h4 class="table-column-info is--header">Player</h4></div><div class="table-column is--large"><h4 class="table-column-info is--header">Team</h4></div><div class="table-column"><h4 class="table-column-info is--header">Record</h4></div><div class="table-column"><h4 class="table-column-info is--header">PCT</h4></div><div class="table-column"><h4 class="table-column-info is--header">LSW</h4></div><div class="table-column is--last"><h4 class="table-column-info is--header">TSTP</h4></div></div>';
            $.each(data.standings, function(_, t) {
                standings_html += '<div class="table-row"><div class="table-column"><h4 class="table-column-info">' +
                    t.rank +
                    '</h4></div><div class="table-column is--la"><h4 class="table-column-info">' +
                    t.manager_name +
                    '</h4></div><div class="table-column is--large is--la"><h4 class="table-column-info">' +
                    t.team_name +
                    '</h4></div><div class="table-column"><h4 class="table-column-info">' +
                    t.record +
                    '</h4></div><div class="table-column"><h4 class="table-column-info">' +
                    t.pct +
                    '</h4></div><div class="table-column"><h4 class="table-column-info">' +
                    t.lowest_score_weeks +
                    '</h4></div><div class="table-column is--last"><h4 class="table-column-info">' +
                    t.total_score_to_par +
                    '</h4></div></div>';
            });

            $("#standings").html(standings_html);
        }
    });
})();