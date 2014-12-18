var CommentsDialog = require('./scenarios/commentsDialog.scenario');
var Auth = require('./scenarios/auth.scenario');

var commentsDialog = new CommentsDialog();
var auth = new Auth();

describe('Testing comments feature', function() {

    beforeEach(function() {
        browser.get('#/alert-details/704');
        browser.ignoreSynchronization = false;
    });

    it('User should be logged in', function() {
        auth.login(function(loggedIn) {
            expect(loggedIn).toBe(true);
        });
    });

    it('Comments button should be displayd after login', function() {
        expect(commentsDialog.modalTrigger.isDisplayed()).toBe(true);
    });

    it('Comments dialog should be displayd after click on comment button', function() {
        commentsDialog.openDialog(function(dialog) {
            expect(dialog.isDisplayed()).toBe(true);
        });
    });

    it('Post comment btn should be disabled if textarea is empty', function() {
        commentsDialog.checkPostBtnState(function(button) {
            expect(button.isEnabled()).toBe(false);
        });
    });

    it('Should insert comment', function() {
        commentsDialog.insertComment(function(comment) {
            expect(comment.getText()).toMatch(/Comment text/);
        });
    });

    it('Should insert 5 more comments', function() {
        commentsDialog.insertComments(5, function(comments) {
            expect(comments.count()).toEqual(6);
        });
    });

    it('More comments button should be displayd', function() {
        commentsDialog.moreCommentsBtnState(function(button) {
            expect(button.isDisplayed()).toBe(true);
        });
    });

    it('Should show all 6 comments after click on "more comments" button', function() {
        commentsDialog.loadMoreComments(function(comments) {
            expect(comments.count()).toEqual(6);
        });
    });

    it('Should remove all comments', function() {
        commentsDialog.removeComments(function(comments) {
            expect(comments.count()).toEqual(0);
        });
    });

    it('User should be logged out', function() {
        auth.logout(function(loggedOut) {
            expect(loggedOut).toBe(true);
        });
    });

});
