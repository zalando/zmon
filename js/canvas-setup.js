domready(function() {
    var stage = new createjs.Stage('hero-canvas'),
        circle = new createjs.Shape();
    circle.graphics.beginFill("DeepSkyBlue").drawCircle(0, 0, 50);
    circle.x = 100;
    circle.y = 100;
    stage.addChild(circle);
    stage.update();

    createjs.Tween
        .get(circle, { loop: true })
        .to({ x: 400 }, 1000, createjs.Ease.getPowInOut(4))
        .to({ alpha: 0, y: 175 }, 500, createjs.Ease.getPowInOut(2))
        .to({ alpha: 0, y: 225 }, 100)
        .to({ alpha: 1, y: 200 }, 500, createjs.Ease.getPowInOut(2))
        .to({ x: 100 }, 800, createjs.Ease.getPowInOut(2));

    createjs.Ticker.setFPS(60);
    createjs.Ticker.addEventListener("tick", stage);
});