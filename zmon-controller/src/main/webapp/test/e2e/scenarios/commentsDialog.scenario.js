var P = protractor.getInstance();
var CommentsDialog = function() {};

CommentsDialog.prototype.modalTrigger = element(by.css('.comment-dialog-trigger'));

CommentsDialog.prototype.dialog = element(by.css('.comment-dialog-trigger .modal-dialog'));

CommentsDialog.prototype.postBtn = element(by.css('.comment-dialog-trigger .modal-dialog form button'));

CommentsDialog.prototype.moreCommentsBtn = element(by.css('.comment-dialog-trigger .modal-dialog .more-comments'));

CommentsDialog.prototype.iComment = element(by.css('.comment-dialog-trigger .modal-dialog form textarea'));

CommentsDialog.prototype.comment = element(by.repeater('comment in comments | orderBy: \'last_modified\'').row(0));

CommentsDialog.prototype.comments = element.all(by.repeater('comment in comments | orderBy: \'last_modified\''));


CommentsDialog.prototype.openDialog = function(cb) {
    self = this;
    this.modalTrigger.click().then(function() {
        if (cb) cb(self.dialog);
    });
};

CommentsDialog.prototype.checkPostBtnState = function(cb) {
    self = this;
    this.openDialog(function() {
        if (cb) cb(self.postBtn);
    });
};

CommentsDialog.prototype.insertComment = function(cb) {
    self = this;
    this.openDialog(function() {
        self.iComment.sendKeys('Comment text');
        self.postBtn.click().then(function() {
            if (cb) cb(self.comment);
        });
    });
};

CommentsDialog.prototype.insertComments = function(numOfComments, cb) {
    self = this;
    var inserted = function(comment) {
        if (cb && comment === numOfComments) cb(self.comments);
    };

    self.openDialog(function() {
        for (var i = 1; i <= numOfComments; i++) {
            self.iComment.sendKeys('Comment text ' + i);
            self.postBtn.click().then(inserted(i));
        }
    });
};

CommentsDialog.prototype.moreCommentsBtnState = function(cb) {
    self = this;
    this.openDialog(function() {
        if (cb) cb(self.moreCommentsBtn);
    });
};

CommentsDialog.prototype.loadMoreComments = function(cb) {
    self = this;
    this.openDialog(function() {
        self.moreCommentsBtn.click().then(function() {
            if (cb) cb(self.comments);
        });
    });
};

CommentsDialog.prototype.removeComments = function(cb) {
    self = this;
    var total = null;

    var remove = function(comment, index) {
        comment.findElement(by.css('.close')).click().then(function() {
            if (cb && index === total) cb(self.comments);
        });
    };

    self.loadMoreComments(function(comments) {
        comments.then(function(comments) {
            total = comments.length;
            for (var index = 0; index < total; index++) {
                remove(comments[index], index + 1);
            }
        });
    });
};

module.exports = CommentsDialog;
