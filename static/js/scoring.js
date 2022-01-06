(function() {
    var req_url = "https://pfgl-psaly.cloud.okteto.net/api/v1/scoreboard";
    $.ajax({
        dataType: "json",
        url: req_url,
        success: function(data) {
            // console.log(data);
            $.each(data.teams, function(_, team) {
                $.each(team.players, function(_, player) {
                    var player_score = format_score(player.score_to_par)
                    var score_html =
                        '<div class="breakdown-table-row"><div class="breakdown-player"><h4 class="scoring-table-info">' + player.player_name +
                        '</h4></div><div class="breakdown-pos"><h4 class="scoring-table-info">' + player.position +
                        '</h4></div><div class="breakdown-score"><h4 class="scoring-table-info">' + player_score +
                        '</h4></div><div class="breakdown-thru"><h4 class="scoring-table-info">' + player.thru +
                        '</h4></div></div>';
                    let team_div = "#" + data.matchup_base_ids[team.manager] + "-table";
                    console.log(team_div);
                    $(team_div).append(score_html);

                    /*
                    m0-p0-info      m0-p1-info
                    m0-p0-table     m0-p1-info

                    */
                });
            });
        }
    });
})();

function format_score(score) {
    if (score > 0) {
        score = "+" + score;
    } else if (score == 0) {
        score = "E";
    }
    return score
}