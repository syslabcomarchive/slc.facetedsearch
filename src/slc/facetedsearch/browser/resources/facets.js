/* Some browsers *ahem* don't implement indexOf. We provide it here for this case */
if (!Array.prototype.indexOf)
{
  Array.prototype.indexOf = function(elt /*, from*/)
  {
    var len = this.length;

    var from = Number(arguments[1]) || 0;
    from = (from < 0)
         ? Math.ceil(from)
         : Math.floor(from);
    if (from < 0)
      from += len;

    for (; from < len; from++)
    {
      if (from in this &&
          this[from] === elt)
        return from;
    }
    return -1;
  };
}

var facets = (function () {
    var currentopen = [],
        show_min = 5;
        show_num = {},
        show_step = 5;

    function toggler(elem, headline) {
        var i = currentopen.indexOf(elem.attr('id'));
        if (i < 0) {
            elem.show();
            headline.addClass('open');
            currentopen.push(elem.attr('id'));
            } else {
            elem.hide();
            headline.removeClass('open');
            currentopen.splice(i);
            }
            }
            return {
currentopen: currentopen,
show_min: show_min,
show_num: show_num,
show_step: show_step,
toggler: toggler
            };
}());

jq(document).ready(function() {
        jq('.submenu_content').not('.open').hide('fast');
        jq('.submenu_title').not('.empty').click(function (e) {
            var targ;
            if (!e) var e = window.event;
            if (e.target) targ = e.target;
            else if (e.srcElement) targ = e.srcElement;
            if (targ.nodeType == 3) // defeat Safari bug
            targ = targ.parentNode;

            //if (!(targ.tagName = "DIV") {}
        topical.toggler(jq('.submenu_content#' + targ.id),
                jq('.submenu_title#' + targ.id));
        });
            jq('.submenu .submenu_more a').click(function(ev) {
                element = jq(ev.target)
                sub = element.parents('.submenu').find('.submenu-lvl2');
                menuid = element.parents('.submenu').attr('id')
                /*if (facets.show_num[menuid] == undefined) {
                  facets.show_num[menuid] = facets.show_min;
                  }*/
                sub.slice(facets.show_num[menuid], facets.show_num[menuid] + facets.show_step)
                .show();
                facets.show_num[menuid] += facets.show_step;
                if (sub.length <= facets.show_num[menuid]) {
                element.parents('.submenu').children('.submenu_more').hide();
                element.parents('.submenu').children('.submenu_less').show();
                }
                });
            jq('.submenu .submenu_less a').click(function(ev) {
                    element = jq(ev.target)
                    sub = element.parents('.submenu').find('.submenu-lvl2');
                    menuid = element.parents('.submenu').attr('id')
                    /*if (facets.show_num[menuid] == undefined) {
                      facets.show_num[menuid] = facets.show_min;
                      }*/
                    sub.slice(facets.show_min, facets.show_num[menuid])
                    .hide();
                    facets.show_num[menuid] = facets.show_min;
                    element.parents('.submenu').children('.submenu_less').hide();
                    element.parents('.submenu').children('.submenu_more').show();
                    });
            //jq('.collapsible').do_search_collapse()
            jq('fieldset.submenu').each(function(index, element) {
                    sub = jq(element).children('.submenu-content').children('.submenu-lvl2');
                    menuid = jq(element).attr('id')
                    if (facets.show_num[menuid] == undefined) {
                    facets.show_num[menuid] = facets.show_min;
                    }
                    if (sub.length > facets.show_num[menuid]) {
                    sub.slice(facets.show_num[menuid]).hide();
            jq(element).children('.submenu_more').show();
        }
    });
    jq('#browsing-menu input[type=checkbox]').click(function() {
        jq('#browsing-menu').submit();
    });
    // get ourselves some fancy sliders
    jq('fieldset.submenu:has(select.facet_range)').each(function(index, element) {
        jq(element).find('select.facet_range').selectToUISlider({ labelSrc: 'text' }).hide();
    });
});

