$(document).ready(function() {
  var currentTime = 0;
  var currentSection = '';
  var updateInterval = 30000;

  var timeToID = function () {
    var date = new Date();
    return 'session-' + date.getHours() + date.getMinutes();
  };

  var update = function () {
    var timeID = timeToID();

    if (timeID !== currentSection) {
      var offset = $('#' + timeID).offset();
      if (offset === undefined) return;
      $('body').animate({ scrollTop: offset.top });
      currentSection = timeID;
    }
  };

  update();
  setInterval(update, updateInterval);
});
