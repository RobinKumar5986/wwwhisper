(function () {
  'use strict';
  var model, view, refresh;

  model = null;

  view = {
    resourcePath : null,
    resourceInfo : null,
    allowedUser : null,
    addResource : null,
    contact : null
  };

  function inArray(value, array) {
    return ($.inArray(value, array) >= 0);
  }

  function removeFromArray(value, array) {
    var idx = $.inArray(value, array);
    if (idx === -1) {
      return;
    }
    array.splice(idx, 1);
  }

  function extractResourcesPaths(resources) {
    return $.map(resources, function(item) {
      return item.path;
    });
  }

  function allResourcesPaths() {
    return extractResourcesPaths(model.resources);
  }

  function accessibleResourcesPaths(userMail) {
    var accessibleResources = $.grep(model.resources, function(resource) {
      return inArray(userMail, resource.allowedUsers);
    });
    return extractResourcesPaths(accessibleResources);
  }

  function resourcePathId(resourceId) {
    return 'resource-path' + resourceId.toString();
  }

  function resourceInfoId(resourceId) {
    return 'resouce-info' + resourceId.toString();
  }

  function findSelectResourceId() {
    return $('#resource-path-list').find('.active').index();
  }

  function mockAjaxCalls() {
    return model !== null && model.mockMode;
  }

  function ajax(method, resource, params, successCallback) {
    if (model !== null) {
      params.csrfToken = model.csrfToken;
    }
    if (!mockAjaxCalls()) {
      $.ajax({
        url: 'acl/' + resource,
        type: method,
        data: JSON.stringify(params),
        dataType: method === 'GET' ?  'json' : 'text',
        success: successCallback,
        error: function(jqXHR) {
          $('body').html(jqXHR.responseText);
        }
      });
    } else {
      successCallback();
    }
  }

  function getModel() {
    ajax('GET', 'model.json', {}, function(result) {
      // TODO: parse json here.
      model = result;
      $('.resources-root').text(model.resourcesRoot);
      refresh();
    });
  }

  function addContact(userMail, onSuccessCallback) {
    ajax('PUT', 'contact', {email: userMail},
         function() {
           model.contacts.push(userMail);
           refresh();
           onSuccessCallback();
         });
  }

  function removeContact(userMail) {
    ajax('DELETE', 'contact', {email: userMail},
         function() {
           $.each(model.resources, function(resourceId, resourceValue) {
             if (inArray(userMail, resourceValue.allowedUsers)) {
               removeFromArray(userMail, resourceValue.allowedUsers);
             }
           });
           removeFromArray(userMail, model.contacts);
           refresh();
         });
  }

  function allowAccessByUser(userMailArg, resourceId) {
    var userMail, resource, grantPermissionCallback;
    userMail = $.trim(userMailArg);
    resource = model.resources[resourceId];
    if (userMail.length === 0
        || inArray(userMail, model.resources[resourceId].allowedUsers)) {
      return;
    }
    grantPermissionCallback = function() {
      ajax('PUT', 'permission', {email: userMail,
                                 path: resource.path},
           function() {
             resource.allowedUsers.push(userMail);
             refresh();
             $('#' + resourceInfoId(resourceId) + ' ' + '.add-allowed-user')
               .focus();
           });
    };

    if (!inArray(userMail, model.contacts)) {
      addContact(userMail, grantPermissionCallback);
    } else {
      grantPermissionCallback();
    }
  }

  // TODO: Fix assymetry (resourceId above, resource here).
  function revokeAccessByUser( userMail, resource) {
    ajax('DELETE', 'permission', {email: userMail,
                               path: resource.path},
           function() {
             removeFromArray(userMail, resource.allowedUsers);
             refresh();
           });
  }

  function addResource(resourcePathArg) {
    var resourcePath = $.trim(resourcePathArg);
    if (resourcePath.length === 0
        || inArray(resourcePath, allResourcesPaths())) {
      return;
    }
    ajax('PUT', 'resource', {path: resourcePath},
         function(escapedPath) {
           model.resources.push({
             'path': escapedPath,
             'allowedUsers': []
           });
           refresh();
           $('#add-resource-input').focus();
         });
  }

  function removeResource(resourceId) {
    ajax('DELETE', 'resource', {path: model.resources[resourceId].path},
         function() {
           model.resources.splice(resourceId, 1);
           var selectResourceId = findSelectResourceId();
           if (selectResourceId === resourceId) {
             refresh(0);
           } else if (selectResourceId > resourceId) {
             refresh(selectResourceId - 1);
           } else {
             refresh(selectResourceId);
           }
         });
  }

  function showResourceInfo(resourceId) {
    $('#' + resourcePathId(resourceId)).addClass('active');
    $('#' + resourceInfoId(resourceId)).addClass('active');
  }

  function highlightAccessibleResources(userMail) {
    $.each(model.resources, function(resourceId, resourceValue) {
      var id = '#' + resourcePathId(resourceId);
      if (inArray(userMail, resourceValue.allowedUsers)) {
        $(id + ' a').addClass('accessible');
      } else {
        $(id + ' a').addClass('not-accessible');
      }
    });
  }

  function highlighResourcesOff() {
    $('#resource-path-list a').removeClass('accessible');
    $('#resource-path-list a').removeClass('not-accessible');
  }

  function showNotifyDialog(to, resources) {
    var body, website, resourcesString, delimiter;
    if (resources.length === 0) {
      body = 'I have shared nothing with you. Enjoy.';
    } else {
      website = 'a website';
      if (resources.length > 1) {
        website = 'websites';
      }
      resourcesString = $.map(resources, function(resourcePath) {
        delimiter = (resourcePath[0] !== '/') ? '/' : '';
        return 'https://' + model.resourcesRoot + delimiter + resourcePath;
      }).join('\n');

      body = 'I have shared ' + website + ' with you.\n'
        + 'Please visit:\n' + resourcesString;
    }
    $('#notify-modal')
      .find('#notify-to').attr('value', to.join(', ')).end()
      .find('#notify-body').text(body).end()
      .modal('show');
  }

  function createResourceInfo(resourceId, allowedUsers) {
    var resourceInfo, allowedUserList;
    resourceInfo = view.resourceInfo.clone(true)
      .attr('id', resourceInfoId(resourceId))
      .find('.add-allowed-user')
      .change(function() {
        allowAccessByUser($(this).val(), resourceId);
      })
      .typeahead({
        'source': model.contacts
      })
      .end();

    allowedUserList = resourceInfo.find('.allowed-user-list');
    $.each(allowedUsers, function(userIdx, userMail) {
      view.allowedUser.clone(true)
        .find('.user-mail').text(userMail).end()
        .find('.remove-user').click(function() {
          revokeAccessByUser(userMail, model.resources[resourceId]);
        }).end()
        .appendTo(allowedUserList);
    });
    resourceInfo.appendTo('#resource-info-list');
  }

  function showContacts() {
    var contact;
    $.each(model.contacts, function(userIdx, userMail) {
      contact = view.contact.clone(true);
      contact.find('.user-mail').text(userMail).end()
        .find('.remove-user').click(function() {
          removeContact(userMail);
        }).end()
        .find('.highlight').hover(function() {
          highlightAccessibleResources(userMail);
        }, highlighResourcesOff).end()
        .find('.notify').click(function() {
          showNotifyDialog([userMail], accessibleResourcesPaths(userMail));
        }).end()
        .appendTo('#contact-list');
    });
  }

  function showResources() {
    $.each(model.resources, function(resourceId, resourceValue) {
      view.resourcePath.clone(true)
        .attr('id', resourcePathId(resourceId))
        .find('.url').attr('href', '#' + resourceInfoId(resourceId)).end()
        .find('.path').text(resourceValue.path).end()
        .find('.remove-resource').click(function(event) {
          // Do not show removed resource info.
          event.preventDefault();
          removeResource(resourceId);
        }).end()
        .find('.notify').click(function() {
          showNotifyDialog(resourceValue.allowedUsers, [resourceValue.path]);
        }).end()
        .appendTo('#resource-path-list');
      createResourceInfo(resourceId, resourceValue.allowedUsers);
    });
    view.addResource.clone(true)
      .find('#add-resource-input').typeahead({
        'source': allResourcesPaths()
      })
      .change(function() {
        addResource($(this).val());
      }).end()
      .appendTo('#resource-path-list');
  }

  refresh = function(selectResourceId) {
    if (typeof selectResourceId === 'undefined') {
      selectResourceId = findSelectResourceId();
    }
    if (selectResourceId === -1) {
      selectResourceId = 0;
    }

    $('#resource-path-list').empty();
    $('#resource-info-list').empty();
    $('#contact-list').empty();

    showResources();
    showContacts();

    showResourceInfo(selectResourceId);
  }


  $(document).ready(function() {
    view.resourcePath = $('#resource-path-list-item').clone(true);
    view.resourceInfo = $('#resource-info-list-item').clone(true);
    view.allowedUser = $('#allowed-user-list-item').clone(true);
    view.resourceInfo.find('#allowed-user-list-item').remove();
    view.addResource = $('#add-resource').clone(true);
    view.contact = $('.contact-list-item').clone(true);

    getModel();
  });

}());
