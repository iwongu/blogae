// Scope to use to access user's photos.
var scope = ['https://www.googleapis.com/auth/photos'];

var pickerApiLoaded = false;
var oauthToken;

// Use the API Loader script to load google.picker and gapi.auth.
function onApiLoad() {
  gapi.load('auth', {'callback': onAuthApiLoad});
  gapi.load('picker', {'callback': onPickerApiLoad});
}

function onAuthApiLoad() {
  window.gapi.auth.authorize(
      {
        'client_id': clientId,
        'scope': scope,
        'immediate': false
      },
      handleAuthResult);
}

function onPickerApiLoad() {
  pickerApiLoaded = true;
  //createPicker();
}

function handleAuthResult(authResult) {
  if (authResult && !authResult.error) {
    oauthToken = authResult.access_token;
    //createPicker();
  }
}

// Create and render a Picker object for picking user Photos.
function createPicker(cb) {
  if (pickerApiLoaded && oauthToken) {
    var picker = new google.picker.PickerBuilder().
        enableFeature(google.picker.Feature.MULTISELECT_ENABLED).
        addView(google.picker.ViewId.PHOTOS).
        addView(google.picker.ViewId.PHOTO_ALBUMS).
        setOAuthToken(oauthToken).
        setDeveloperKey(developerKey).
        setCallback(cb).
        build();
    picker.setVisible(true);
  }
}
