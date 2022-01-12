(function() {
    var req_url = "https://pfgl-psaly.cloud.okteto.net/api/v1/scoreboard";
    $.ajax({
        dataType: "json",
        url: req_url,
        success: function(data) {

            $("#tournament-name").html('<h1 class="page-mainheading">' + data.tournament_details.tournament_name + '</h1>')
            $("#course-name").html('<h2 class="tournament-info-h2">'+ data.tournament_details.course_name +'</h2>')
            $("#course-info").html('<h4 class="leaderboard is--left">' + data.tournament_details.course_details + '<br></h4>')
            $("#tournament-date").html('<h4 class="leaderboard">' + data.tournament_details.dates + '<br></h4>')
            
            $.each(data.teams, function(_, team) {
                // #m0-p0-info
                let matchup_info_div = `#${data.matchup_base_ids[team.manager]}-info`;
                var info_html = '<div class="scoring-team-left"><div class="scoring-team-img"><img src="'+
                    team.logo_url +
                    '" loading="lazy" alt="" class="image-2"></div><h2 class="scoring-team-name">' +
                    team.manager_name +
                    '</h2><h4 class="scoring-team-record">' +
                    team.record +
                    '</h4></div><div class="scoring-team-right"><div class="scoring-team-topar"><h2 class="scoring-team-topar-h2">' +
                    format_score(team.team_score) +
                    '</h2></div></div>';
                    
                $(matchup_info_div).html(info_html);

                let team_name_div = `#${data.matchup_base_ids[team.manager]}-team`
                let team_num_players_div = `#${data.matchup_base_ids[team.manager]}-players`

                $(team_name_div).html('<h4 class="scoring-breakdown-h4 is--left">' + team["team_name"] + '</h4>')
                $(team_num_players_div).html('<h4 class="scoring-breakdown-h4 is--right">' + team["players"].length + ' Players</h4>')

                $.each(team.players, function(_, player) {
                    let player_score = format_score(player.score_to_par)
                    var score_html =
                        '<div class="breakdown-table-row"><div class="breakdown-player"><h4 class="scoring-table-info">' +
                        player.player_name +
                        '</h4></div><div class="breakdown-pos"><h4 class="scoring-table-info">' +
                        player.position +
                        '</h4></div><div class="breakdown-score"><h4 class="scoring-table-info">' +
                        player_score +
                        '</h4></div><div class="breakdown-round"><h4 class="scoring-table-info">' +
                        player.today +
                        '</h4></div><div class="breakdown-thru"><h4 class="scoring-table-info">' +
                        player.thru +
                        '</h4></div></div>';
                    // #m0-p0-table
                    let matchup_table_div = `#${data.matchup_base_ids[team.manager]}-table`;
                    // console.log(matchup_table_div);
                    $(matchup_table_div).append(score_html);
                });
            });

            // Set image for who is winnning
            // 10 team league so 5, this probably shouldn't be hard-coded but oh well
            for (let i = 0; i < 5; i++) {
                let matchup_winning_div = `#m${i}-win`;
                let winning_url = data.matchup_winning[`m${i}`]["logo_url"];
                let lowercase_winning_name = data.matchup_winning[`m${i}`]["name"];
                // capitalize name
                let winning_name = lowercase_winning_name[0].toUpperCase() + lowercase_winning_name.slice(1);

                var winning_html = '<div class="scoring-team-img is--center"><img src="' +
                    winning_url +
                    '" loading="lazy" alt="" class="image-2"></div><h4 class="scoring-winning-name">' +
                    winning_name + 
                    '</h4></div>';
                $(matchup_winning_div).append(winning_html);
            }
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