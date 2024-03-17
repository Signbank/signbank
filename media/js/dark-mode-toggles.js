

function toggle_dark_mode() {
  $(".body").each(function () {
        if ($(this).hasClass("body-light")) {
            $(this).removeClass("body-light");
            $(this).addClass("body-dark");
        } else if ($(this).hasClass("body-dark")) {
            $(this).removeClass("body-dark");
            $(this).addClass("body-light");
        }
  });
  $(".modal").each(function () {
        if ($(this).hasClass("dark-mode")) {
            $(this).removeClass("dark-mode");
        } else {
            $(this).addClass("dark-mode");
        }
  });
  $(".panel-default").each(function () {
        if ($(this).hasClass("panel-light")) {
            $(this).removeClass("panel-light");
            $(this).addClass("panel-default-dark");
        } else if ($(this).hasClass("panel-default-dark")) {
            $(this).removeClass("panel-default-dark");
            $(this).addClass("panel-light");
        }
  });
  $(".panel-heading").each(function () {
        if ($(this).hasClass("panel-light")) {
            $(this).removeClass("panel-light");
            $(this).addClass("panel-heading-dark");
        } else if ($(this).hasClass("panel-heading-dark")) {
            $(this).removeClass("panel-heading-dark");
            $(this).addClass("panel-light");
        }
  });
  $(".collapse").each(function () {
        if ($(this).hasClass("collapse-light")) {
            $(this).removeClass("collapse-light");
            $(this).addClass("collapse-dark");
        } else if ($(this).hasClass("collapse-dark")) {
            $(this).removeClass("collapse-dark");
            $(this).addClass("collapse-light");
        }
  });
  $(".well").each(function () {
        if ($(this).hasClass("well-light")) {
            $(this).removeClass("well-light");
            $(this).addClass("well-dark");
        } else if ($(this).hasClass("well-dark")) {
            $(this).removeClass("well-dark");
            $(this).addClass("well-light");
        }
  });
  $(".navbar").each(function () {
        if ($(this).hasClass("navbar-light")) {
            $(this).removeClass("navbar-light");
            $(this).addClass("navbar-dark");
        } else if ($(this).hasClass("navbar-dark")) {
            $(this).removeClass("navbar-dark");
            $(this).addClass("navbar-light");
        }
  });
  $(".navbar-nav").each(function () {
        if ($(this).hasClass("navbar-nav-light")) {
            $(this).removeClass("navbar-nav-light");
            $(this).addClass("navbar-nav-dark");
        } else if ($(this).hasClass("navbar-nav-dark")) {
            $(this).removeClass("navbar-nav-dark");
            $(this).addClass("navbar-nav-light");
        }
  });
  $(".navbar-form").each(function () {
        if ($(this).hasClass("navbar-form-light")) {
            $(this).removeClass("navbar-form-light");
            $(this).addClass("navbar-form-dark");
        } else if ($(this).hasClass("navbar-form-dark")) {
            $(this).removeClass("navbar-form-dark");
            $(this).addClass("navbar-form-light");
        }
  });
  $(".navbar-text").each(function () {
        if ($(this).hasClass("navbar-text-light")) {
            $(this).removeClass("navbar-text-light");
            $(this).addClass("navbar-text-dark");
        } else if ($(this).hasClass("navbar-text-dark")) {
            $(this).removeClass("navbar-text-dark");
            $(this).addClass("navbar-text-light");
        }
  });
  $(".dropdown").each(function () {
        if ($(this).hasClass("dropdown-light")) {
            $(this).removeClass("dropdown-light");
            $(this).addClass("dropdown-dark");
        } else if ($(this).hasClass("dropdown-dark")) {
            $(this).removeClass("dropdown-dark");
            $(this).addClass("dropdown-light");
        }
  });
  $(".dropdown-menu").each(function () {
        if ($(this).hasClass("dropdown-menu-light")) {
            $(this).removeClass("dropdown-menu-light");
            $(this).addClass("dropdown-menu-dark");
        } else if ($(this).hasClass("dropdown-menu-dark")) {
            $(this).removeClass("dropdown-menu-dark");
            $(this).addClass("dropdown-menu-light");
        }
  });
  $(".text-container").each(function () {
        if ($(this).hasClass("text-container-light")) {
            $(this).removeClass("text-container-light");
            $(this).addClass("text-container-dark");
        } else if ($(this).hasClass("text-container-dark")) {
            $(this).removeClass("text-container-dark");
            $(this).addClass("text-container-light");
        }
  });
  $(".interface-language").each(function () {
        if ($(this).hasClass("interface-language-light")) {
            $(this).removeClass("interface-language-light");
            $(this).addClass("interface-language-dark");
        } else if ($(this).hasClass("interface-language-dark")) {
            $(this).removeClass("interface-language-dark");
            $(this).addClass("interface-language-light");
        }
  });
  $(".input-group").each(function () {
        if ($(this).hasClass("input-group-light")) {
            $(this).removeClass("input-group-light");
            $(this).addClass("input-group-dark");
        } else if ($(this).hasClass("input-group-dark")) {
            $(this).removeClass("input-group-dark");
            $(this).addClass("input-group-light");
        }
  });
  $(".btn-default").each(function () {
        if ($(this).hasClass("btn-default-light")) {
            $(this).removeClass("btn-default-light");
            $(this).addClass("btn-default-dark");
        } else if ($(this).hasClass("btn-default-dark")) {
            $(this).removeClass("btn-default-dark");
            $(this).addClass("btn-default-light");
        }
  });
  $("tbody").each(function () {
        if ($(this).hasClass("tbody-light")) {
            $(this).removeClass("tbody-light");
            $(this).addClass("tbody-dark");
        } else if ($(this).hasClass("tbody-dark")) {
            $(this).removeClass("tbody-dark");
            $(this).addClass("tbody-light");
        }
  });
  $("thead").each(function () {
        if ($(this).hasClass("thead-light")) {
            $(this).removeClass("thead-light");
            $(this).addClass("thead-dark");
        } else if ($(this).hasClass("thead-dark")) {
            $(this).removeClass("thead-dark");
            $(this).addClass("thead-light");
        }
  });
  $("td").each(function () {
        if ($(this).hasClass("td-light")) {
            $(this).removeClass("td-light");
            $(this).addClass("td-dark");
        } else if ($(this).hasClass("td-dark")) {
            $(this).removeClass("td-dark");
            $(this).addClass("td-light");
        }
  });
  $(".th").each(function () {
        if ($(this).hasClass("th-light")) {
            $(this).removeClass("th-light");
            $(this).addClass("th-dark");
        } else if ($(this).hasClass("th-dark")) {
            $(this).removeClass("th-dark");
            $(this).addClass("th-light");
        }
  });
  $(".table-condensed").each(function () {
        if ($(this).hasClass("table-condensed-light")) {
            $(this).removeClass("table-condensed-light");
            $(this).addClass("table-condensed-dark");
        } else if ($(this).hasClass("table-condensed-dark")) {
            $(this).removeClass("table-condensed-dark");
            $(this).addClass("table-condensed-light");
        }
  });
  $(".search-form").each(function () {
        if ($(this).hasClass("search-form-light")) {
            $(this).removeClass("search-form-light");
            $(this).addClass("search-form-dark");
        } else if ($(this).hasClass("search-form-dark")) {
            $(this).removeClass("search-form-dark");
            $(this).addClass("search-form-light");
        }
  });
  $(".span-text").each(function () {
        if ($(this).hasClass("span-text-light")) {
            $(this).removeClass("span-text-light");
            $(this).addClass("span-text-dark");
        } else if ($(this).hasClass("span-text-dark")) {
            $(this).removeClass("span-text-dark");
            $(this).addClass("span-text-light");
        }
  });
}

function set_dark_mode(){
    $.ajax({
        url : set_dark_mode_url,
        type: 'POST',
        data: {},
        datatype: "json"
     });
     toggle_dark_mode();
}
