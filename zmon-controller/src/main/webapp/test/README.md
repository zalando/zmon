# Installation and running tests (ZMON 2.0)

## INSTALLATION (common for Protractor e2e + Karma Unit tests)

* Install node.js
    * Run `curl https://raw.github.com/creationix/nvm/master/install.sh | sh`
    * Put the `[[ -s $HOME/.nvm/nvm.sh ]] && . $HOME/.nvm/nvm.sh` in your profile (.bashrc, .bash_profile) if it's not already there and do `source .bashrc`
    * Run `nvm install 0.10.23`
    * To set default node version run `nvm alias default 0.10.23`
    * After installation type `node -v` in your terminal to check if everything works :)
* Run `npm install -g grunt && npm install -g grunt-cli`
* Navigate to `cd path/to/zmon2/zmon-controller/src/main/webapp`
* Run `npm install` to install all dependencies

## PROTRACTOR (e2e testing)

### Run tests

* Open new tab in your terminal and navigate to `cd path/to/zmon2/zmon-controller/src/main/webapp`
* Run `grunt init` (this will start selenium webdriver)
* Again open new tab in your terminal and navigate to `cd path/to/zmon2/zmon-controller/src/main/webapp`
* Run tests
    * run `grunt run-e2e` - for single run of protractor e2e tests
    * run `grunt run-unit` - for single run of karma unit tests
    * run `grunt watch` - for watching code changes and auto triggering of tests
    * run `grunt jenkins-e2e` - for single run of protractor e2e tests on QA selenium server (report .xml files are saved under ci/)
    * run `grunt jenkins-unit` - for single run of karma unit tests on QA selenium server (report .xml file saved under ci/)


### Notes on Protractor and WebDriverJS (General)

### Control flow

* Tests are written with the WebDriver API, which communicates with a Selenium server to control the browser under test.
* Protractor is a wrapper around WebDriverJS. WebDriverJS (and thus, Protractor) APIs are entirely asynchronous. All functions return promises.
* WebDriverJS maintains a queue of pending promises, called the control flow, to keep execution organized.
* Protractor adapts Jasmine so that each spec automatically waits until the control flow is empty before exiting. This means you don't need to worry about calling runs() and waitsFor() blocks.
* Thus this works:

    expect(name.getText()).toEqual('Jane Doe');

and adds an expectation task to the control flow, which will run after the other tasks.

### Setup

See [https://github.com/angular/protractor/blob/master/docs/getting-started.md#setup-and-config]

### Protractor

Protractor exposes several global variables.

* `browser` this is the a wrapper around an instance of webdriver. Used for navigation and page-wide information.

* `element` is a helper function for finding and interacting with elements on the page you are testing.

* `by` is a collection of element locator strategies. For example, elements can be found by CSS selector, by ID, or by the attribute they are bound to with ng-model.

The `element` method searches for an element on the page. It requires one parameter, a locator strategy for locating the element. Protractor offers Angular specific strategies:
	* `by.binding` searches for elements by matching binding names, either from `ng-bind` or `{{}}` notation in the template.
    * `by.model` searches for elements by input ng-model.
    * `by.repeater` searches for `ng-repeat` elements. For example, `by.repeater('phone in phones').row(11).column('price')` returns the element in the 12th row (0-based) of the `ng-repeat = "phone in phones"` repeater with the binding matching `{{phone.price}}`.
    * `by.id`
    * `by.css`
    * `by.tagName`

> NOTE: `element` returns an ElementFinder. This is an object which allows you to interact with the element on your page, but since all interaction with the browser must be done over webdriver, it is important to remember that this is not a DOM element. You can interact with it with methods such as `sendKeys`, `getText`, and `click`.

### Setup of tested system

* Protractor uses real browsers to run its tests, so it can connect to anything that your browser can connect to. All Protractor needs is the URL.
* If your page does manual bootstrap Protractor will not be able to load your page using `browser.get`. Instead, use the base webdriver instance - `browser.driver.get`. This means that Protractor does not know when your page is fully loaded, and you may need to add a wait statement to make sure your tests avoid race conditions.
* If your page uses `$timeout` for polling Protractor will not be able to tell when your page is ready. Consider using `$interval` instead of `$timeout` and see [this issue](https://github.com/angular/protractor/issues/49) for further discussion.


### Examples

[https://github.com/angular/protractor/blob/master/spec/basic/findelements_spec.js]

## KARMA (unit-testing)

### Installation

You need to install some node modules; run at the root of the webapp/ folder:

$ npm install

This should install under node_modules/ the folders for the modules you see in `packages.json` under `devDependencies`

### Configuration

The configuration file is under `test/karma.connf.js` and will run karma by default on localhost on the default port 9876 using Chrome. For this you need to add the following line in your ~/.bashrc so as to set the $CHROME_BIN env variable to the path of your chrome browser executable:

export CHROME_BIN='/usr/bin/chromium-browser'

### Tests

All unit tests are located at `test/unit` and have names *.spec.js (see `files` property in `karma.conf.js`).

## TIPS

### Jasmine matchers

* toBe: represents the exact equality (===) operator.
* toEqual: represents the regular equality (==) operator.
* toMatch: calls the RegExp match() method behind the scenes to compare string data.
* toBeDefined: opposite of the JS "undefined" constant.
* toBeUndefined: tests the actual against "undefined".
* toBeNull: tests the actual against a null value - useful for certain functions that may return null, like those of regular expressions (same as toBe(null))
* toBeTruthy: simulates JavaScript boolean casting.
* toBeFalsy: like toBeTruthy, but tests against anything that evaluates to false, such as empty strings, zero, undefined, etc…
* toContain: performs a search on an array for the actual value.
* toBeLessThan/toBeGreaterThan: for numerical comparisons.
* toBeCloseTo: for floating point comparisons.
* toThrow: for catching expected exceptions.