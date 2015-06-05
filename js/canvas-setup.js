// domready(function() {
//     var stage = new createjs.Stage('hero-canvas'),
//         circle = new createjs.Shape();
//     circle.graphics.beginFill('Orange').drawCircle(0, 0, 50);
//     circle.x = 100;
//     circle.y = 100;
//     stage.addChild(circle);
//     stage.update();

//     createjs.Tween
//         .get(circle, { loop: true })
//         .to({ scaleX: 2, scaleY: 2 }, 1000, createjs.Ease.getPowInOut(2))
//         .to({ scaleX: 1, scaleY: 1}, 1000, createjs.Ease.getPowInOut(2));

//     createjs.Ticker.setFPS(60);
//     createjs.Ticker.addEventListener("tick", stage);
// });
// 
domready(function() {
    var stage = new createjs.Stage('hero-canvas'),
        line = new createjs.Shape();
    line
        .graphics
        .setStrokeStyle(1)
        .beginStroke('Orange')
        .moveTo(0, 100)
        .lineTo(100, 0);
    stage.addChild(line);
    stage.update();
    // stage.cache();
    // stage.updateCache();
})