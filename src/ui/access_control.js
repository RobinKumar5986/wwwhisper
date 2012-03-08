(function () {
  'use strict';
  var model, view, refresh;

  model = {
    resourcesRoot : 'mixedbit.org/protected',
    resources : [
      {
        path: '/photo-album',
        allowedUsers: [
          'vito@genco-pura.com',
          'michael@genco-pura.com',
          'sonny@genco-pura.com',
          'clemenza@genco-pura.com',
          'alice@wonderland.org'
        ]
      },
      {
        path: '/work-wiki',
        allowedUsers: [
          'tony@montata-co.com',
          'sosa@plantation.bo',
          'clemenza@genco-pura.com',
          'alice@wonderland.org'
        ]
      },
      {
        path: '/conference/papers',
        allowedUsers: [
          'profFoo@universityA.org',
          'drBar@universityB.com',
          'msBaz@universityC.edu',
          'alice@wonderland.org'
        ]
      },
      {
        path: '/conference/upload-photos',
        allowedUsers: [
          'drBar@universityB.com',
          'alice@wonderland.org'
        ]
      },
      {
        path: '/wwwhisper',
        allowedUsers: [
          'alice@wonderland.org'
        ]
      }
    ],
    contacts : [
      'alice@wonderland.org',
      'vito@genco-pura.com',
      'michael@genco-pura.com',
      'sonny@genco-pura.com',
      'clemenza@genco-pura.com',
      'tony@montata-co.com',
      'sosa@plantation.bo',
      'profFoo@universityA.org',
      'drBar@universityB.com',
      'msBaz@universityC.edu',
    ]
  };

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

  function allowAccessByUser(resourceId, userMailArg) {
    var userMail = $.trim(userMailArg);
    if (userMail.length === 0
        || inArray(userMail, model.resources[resourceId].allowedUsers)) {
      return;
    }
    if (inArray(userMail, model.contacts)) {
      model.contacts.push(userMail);
    }
    model.resources[resourceId].allowedUsers.push(userMail);
    refresh();
    $('#' + resourceInfoId(resourceId) + ' ' + '.add-allowed-user').focus();
  }

  function addResource(resourcePathArg) {
    var resourcePath = $.trim(resourcePathArg);
    if (resourcePath.length === 0
        || inArray(resourcePath, allResourcesPaths())) {
      return;
    }
    model.resources.push({
      'path': resourcePath,
      'allowedUsers': []
    });
    refresh();
    $('#add-resource-input').focus();
  }

  function revokeAccessByUser(userMail, resource) {
    removeFromArray(userMail, resource.allowedUsers);
    refresh();
  }

  function removeContact(userMail) {
    removeFromArray(userMail, model.contacts);
    $.each(model.resources, function(resourceId, resourceValue) {
      if (inArray(userMail, resourceValue.allowedUsers)) {
        removeFromArray(userMail, resourceValue.allowedUsers);
      }
    });
    refresh();
  }

  function removeResource(resourceId) {
    model.resources.splice(resourceId, 1);
    var selectResourceId = findSelectResourceId();
    if (selectResourceId === resourceId) {
      refresh(0);
    } else if (selectResourceId > resourceId) {
      refresh(selectResourceId - 1);
    } else {
      refresh(selectResourceId);
    }
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
      .find('#notify-body').html(body).end()
      .modal('show');
  }

  function createResourceInfo(resourceId, allowedUsers) {
    var resourceInfo, allowedUserList;
    resourceInfo = view.resourceInfo.clone(true)
      .attr('id', resourceInfoId(resourceId))
      .find('.add-allowed-user')
      .change(function() {
        allowAccessByUser(resourceId, $(this).val());
      })
      .typeahead({
        'source': model.contacts
      })
      .end();

    allowedUserList = resourceInfo.find('.allowed-user-list');
    $.each(allowedUsers, function(userIdx, userMail) {
      view.allowedUser.clone(true)
        .find('.user-mail').html(userMail).end()
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
      contact.find('.user-mail').html(userMail).end()
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
        .find('.path').html(resourceValue.path).end()
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
    $('.resources-root').html(model.resourcesRoot);
    view.resourcePath = $('#resource-path-list-item').clone(true);
    view.resourceInfo = $('#resource-info-list-item').clone(true);
    view.allowedUser = $('#allowed-user-list-item').clone(true);
    view.resourceInfo.find('#allowed-user-list-item').remove();
    view.addResource = $('#add-resource').clone(true);
    view.contact = $('.contact-list-item').clone(true);
    refresh();
  });

}());
