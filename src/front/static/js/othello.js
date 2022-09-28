function Chessboard(){
    var oo = this;
    var pieces;
    var piecesnum;
    var side;

    oo.toDown = null;
    
    function bindEvent(td)	//绑定点击事件
	{
		for(var i=0; i<64; i++)
			(function (i){
				td[i].onclick = function (){
					if (pieces[i].className=="prompt"){
						oo.toDown(i);
					}
						
				}
			})(i);
		td = undefined;
	}

    oo.create = function ()		//创建棋盘
	{
		var obj = document.getElementById("chessboard");
		var html = "<table>";
		for (var i=0; i<8; i++)
		{
			html += "<tr>";
			for (var j=0; j<8; j++)
				html += "<td class='bg"+(j+i)%2+"'><div></div></td>";
			html += "</tr>";
		}
		html += "</table>";
		obj.innerHTML = html;
		pieces = obj.getElementsByTagName("div");
		bindEvent(obj.getElementsByTagName("td"));

		piecesnum = document.getElementById("console").getElementsByTagName("span");
		side = {
			"1": document.getElementById("side1"),
			"-1": document.getElementById("side2")
		};
	}

    oo.update = function (m)		//更新棋盘
	{
		for (var i = 0; i < 64; i++)
			pieces[i].className = ["white","","black"][m[i] + 1];
	
		for (var n in m.next)
			pieces[m.next[n]].className = "prompt";
		
		for (var i = 0; i < m.newRev.length; i++)
			pieces[m.newRev[i]].className += " reversal";
	
		if (m.newPos!=-1)
			pieces[m.newPos].className += " newest";
		
        piecesnum[0].innerHTML = m.black;
		piecesnum[1].innerHTML = m.white;
		
        side[m.side].className = "cbox side";
		side[-m.side].className = "cbox";
	}
}

function Othello(){
    var oo = this;
    var map = [];
    var pass_obj = document.getElementById("pass");

    oo.play = function(){
        map = []
        for(var i = 0; i < 64; i++)
            map[i] = 0;
        map[28] = map[35] = 1;			//黑子为 1
        map[27] = map[36] = -1;			//白子为 -1
        map.black = 2;
        map.white = 2;
        map.side = 1;		//当前执棋方
        map.newPos = -1;	//最新下子的位置
		map.newRev = [];	//最新反转棋子的位置
		map.next = [19, 26, 37, 44];		//下一步可走棋的反转棋子
		
        update();
    }

    function update(){
        setPassStatus(false);
        board.update(map);
    }

    oo.goChess = function(n){
		$.ajax({
			url: "/player/" + map.side,
			type: "get",
			data:{
				"point": n
			},
			dataType: "json",
			success:function(res){
				if(res.error == true){
					alert("error!");
				}else{
					map.black = 0;
					map.white = 0;
					for(var i = 0; i < 64; i++){
						if(res.board[i] == 1) {
							map[i] = 1;
							map.black++;
						}
						else if(res.board[i] == 2) {
							map[i] = -1;
							map.white++;
						} 
						else map[i] = 0;
					}
					if(res.turn == 1){
						map.side = 1;
					}else{
						map.side = -1;
					}
					map.newPos = n;
					map.next = res.available;
					map.newRev = [];
					update();
					
					if(res.is_end){
						alert("game end\nblack:" + map.black + ",white:" + map.white);
						return;
					}else{
						if(map.side == -1){
							oo.goChess(-1);
						}
					}
				}
			},
			error:function(){
				alert('something wrong with the nextwork!');
				return;
			}
		})
    }

    function setPassStatus(flag)		//设置pass状态
	{
		pass_obj.style.display = flag ? "block" : "none";
		if(flag)
            pass_obj.innerHTML = map.side == 1 ? "白方无棋可下，黑方继续下子":"黑方无棋可下，白方继续下子";
	}
}

var board = new Chessboard();
var othe = new Othello();
board.create();
board.toDown = othe.goChess;

document.getElementById("play").onclick = function() {
	$.ajax({
		url: "/restart",
		type: "get",
		success:function(){
			othe.play();
		},
		error:function(){
			alert("start error!");
		}
	})
	
};

document.getElementById("explain").onclick = function() {
	alert("黑白棋游戏说明\n【简介】\n黑白棋又叫反棋(Reversi)、奥赛罗棋(Othello)、苹果棋或翻转棋。游戏通过相互翻转对方的棋子，最后以棋盘上谁的棋子多来判断胜负。\n【规则】\n1．黑方先行，双方交替下棋。\n2．新落下的棋子与棋盘上已有的同色棋子间，对方被夹住的所有棋子都要翻转过来。可以是横着夹，竖着夹，或是斜着夹。夹住的位置上必须全部是对手的棋子，不能有空格。\n3．新落下的棋子必须翻转对手一个或多个棋子，否则就不能落子。\n4．如果一方没有合法棋步，也就是说不管他下到哪里，都不能至少翻转对手的一个棋子，那他这一轮只能弃权，而由他的对手继续落子直到他有合法棋步可下。\n5．如果一方至少有一步合法棋步可下，他就必须落子，不得弃权。\n6．当棋盘填满或者双方都无合法棋步可下时，游戏结束。结束时谁的棋子最多谁就是赢家。\n\nPS: 本游戏最好用Chrome浏览器远行，以达到最高棋力。\n");
};