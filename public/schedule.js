$(document).ready(function() {
  var currentTime = 0;
  var currentSection = '';
  var updateInterval = 30000;

  // if current section is less than 
  var getFormattedTime = function () {
    return date.getHours() * 100 + date.getMinutes();
  };

  var timeToID = function () {
    var date = new Date();
    return 'session-' + currentTime;
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
