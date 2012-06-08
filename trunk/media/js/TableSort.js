$.fn.extend({
    sorttable: function (setting) {
        var configer = $.fn.extend({
            sorttingMsg: "sorting¡­¡­",
            sorttingMsgColor: "#FFF",
            allowMask: true,
            maskOpacity: "0.5",
            maskColor: "#000",
            ascImgUrl: "",
            ascImgSize: "8px",
            descImgUrl: "",
            descImgSize: "8px",
            onSorted: null
        }, setting);
        var extObj = $(this);
        var lock = false;
        var sortOrder = {
            byAsc: "asc",
            byDesc: "desc"
        };
        var myAttrs = {
            order: "order",
            by: "by",
            sort: "sort"
        };
        var headCells = extObj.find("tr[role='head']>[" + myAttrs.sort + "='true']");
        headCells.each(function () {
            if (configer.ascImgUrl != "" && configer.descImgUrl != "") {
                $("&nbsp;<img class='asc' src='" + configer.ascImgUrl + "' style='width:" + configer.ascImgSize + "; height:" + configer.ascImgSize + ";display:none;' title='up' alt='up'/>").appendTo($(this));
                $("&nbsp;<img class='desc' src='" + configer.descImgUrl + "' style='width:" + configer.descImgSize + "; height:" + configer.descImgSize + ";display:none;' title='desc' alt='desc'/>").appendTo($(this));
            }
            else {
                $("&nbsp;<span class='asc' style='width:12px; height:12px;display:none;' title='up'>&#118;</span>").appendTo($(this));
                $("&nbsp;<span class='desc' style='width:12px; height:12px;display:none;' title='desc'>&#94;</span>").appendTo($(this));
            }
            $(this).css("cursor", "default");
        });
        headCells.click(function () {
            var thisCell = $(this);
            if (lock == false) {
                lock = true;
                if (configer.allowMask) {
                    var tw = extObj.outerWidth();
                    var th = extObj.outerHeight();
                    var tOffSet = extObj.offset();
                    var tTop = tOffSet.top;
                    var tLeft = tOffSet.left;
                    var mark = $("<div></div>").attr("id", "TableSort_Mark").css("background-color", configer.maskColor).css("position", "absolute").css("top", tTop + "px").css("left", tLeft + "px").css("opacity", configer.maskOpacity).css("z-index", "9999").css("width", tw + "px").css("height", th + "px");
                    mark.html("<h3 id='TableSort_Sortting' style='opacity:1;color:" + configer.sorttingMsgColor + ";padding:36px 0 0 0;text-align:center;'>" + configer.sorttingMsg + "</h3>");
                    mark.appendTo($("body"));
                    window.setTimeout(function () {
                        SetColumnOrder(thisCell);
                        FireHandleAfterSortting(thisCell);
                        lock = false;
                        mark.remove();
                    }, 100);
                }
                else {
                    SetColumnOrder(thisCell);
                    FireHandleAfterSortting(thisCell);
                    lock = false;
                }
                headCells.attr(myAttrs.order, false);
                thisCell.attr(myAttrs.order, true);
                var by = thisCell.attr(myAttrs.by);
                thisCell.attr(myAttrs.by, (by == sortOrder.byAsc ? sortOrder.byDesc : sortOrder.byAsc));
            }
        });
        function FireHandleAfterSortting(sortCell) {
            if (configer.onSorted != null) {
                configer.onSorted(sortCell);
            }
        }
        function SetColumnOrder(headCell) {
            var by = headCell.attr(myAttrs.by);
            var index = headCell.index();
            var rs = extObj.find("tr[role!='head']");
            rs.sort(function (r1, r2) {
                var a = $.trim($(r1).children("td").eq(index).text());
                var b = $.trim($(r2).children("td").eq(index).text());
                if (a == b) {
                    return 0;
                }
                var isDt = IsTime(a) && IsTime(b);
                if (isDt) {
                    var dt1 = new Date(a.replace(/-/g, "/"));
                    var dt2 = new Date(b.replace(/-/g, "/"));
                    if (dt1.getTime() > dt2.getTime()) {
                        return (by == sortOrder.byAsc) ? 1 : -1;
                    }
                    else {
                        return (by == sortOrder.byAsc) ? -1 : 1;
                    }
                }
                else if (isNaN(a) || isNaN(b)) {
                    return (by == sortOrder.byAsc) ? a.localeCompare(b) : b.localeCompare(a);
                }
                else {
                    if (a - b > 0) {
                        return (by == sortOrder.byAsc) ? 1 : -1;
                    }
                    else {
                        return (by == sortOrder.byAsc) ? -1 : 1;
                    }
                }

            });
            extObj.find("tr[role!='head']").remove();
            extObj.append(rs);
            headCells.children(".asc,.desc").hide();
            if (by == sortOrder.byAsc) {
                headCell.children(".asc").show();
            }
            else {
                headCell.children(".desc").show();
            }
        }
        function IsTime(dateString) {
            dateString = $.trim(dateString);
            if (dateString == null && dateString.length == 0) {
                return false;
            }
            dateString = dateString.replace(/\//g, "-");
            var reg = /^(\d{1,4})(-|\/)(\d{1,2})\2(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2})$/;
            var r = dateString.match(reg);
            if (r == null) {
                var reg = /^(\d{1,4})(-|\/)(\d{1,2})\2(\d{1,2})$/;
                var r = dateString.match(reg);
            }
            return r != null;
        }
    }
});
