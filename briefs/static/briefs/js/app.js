/* AI Brief Generator — jQuery front end.
 * States: empty → loading → success | error. All model output is inserted with .text().
 */
(function ($) {
  "use strict";

  var API_URL = "/api/briefs/";
  var EVENTS_URL = "/api/events/";
  var REQUEST_TIMEOUT_MS = 90000;
  var FIELDS = ["brand_name", "platform", "goal", "tone", "product_note"];
  var LABELS = {
    platform: { instagram: "Instagram", tiktok: "TikTok", ugc: "UGC" },
    goal: { awareness: "Awareness", conversions: "Conversions", content_assets: "Content Assets" },
    tone: { professional: "Professional", friendly: "Friendly", playful: "Playful" }
  };
  var CLIENT_ERRORS = {
    brand_name: "Enter your brand name.",
    platform: "Choose a platform.",
    goal: "Choose a goal.",
    tone: "Choose a tone."
  };
  var ICON_CHECK = '<svg class="li-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  var ICON_X = '<svg class="li-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>';

  var $form = $("#brief-form");
  var $submit = $("#generate-btn");
  var $result = $("#result");
  var $live = $("#live-region");
  var state = { status: "empty", lastPayload: null, requestId: null, edited: false, pending: null };

  // ---------------------------------------------------------------- helpers
  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : "";
  }

  $.ajaxSetup({
    contentType: "application/json",
    dataType: "json",
    beforeSend: function (xhr) { xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken")); }
  });

  var EDIT_MODE = (function () {
    try {
      var el = document.createElement("div");
      el.contentEditable = "plaintext-only";
      return el.contentEditable === "plaintext-only" ? "plaintext-only" : "true";
    } catch (e) {
      return "true";
    }
  })();

  function announce(message) {
    $live.text("");
    window.setTimeout(function () { $live.text(message); }, 50);
  }

  var toastTimer = null;
  function toast(message, isError) {
    var $toast = $("#toast");
    $toast.toggleClass("ds-toast--error", !!isError).toggleClass("ds-toast--success", !isError);
    $("#toast-message").text(message);
    $toast.prop("hidden", false);
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () { $toast.prop("hidden", true); }, 2600);
  }

  function track(event) {
    if (!state.requestId) { return; }
    $.ajax({ url: EVENTS_URL, method: "POST", dataType: "text",
      data: JSON.stringify({ event: event, request_id: state.requestId }) });
  }

  // ---------------------------------------------------------------- state
  function setState(status) {
    state.status = status;
    $result.find("[data-state]").each(function () {
      var $panel = $(this);
      var active = $panel.data("state") === status;
      $panel.prop("hidden", !active);
      if ($panel.data("state") === "loading") { $panel.attr("aria-hidden", active ? "false" : "true"); }
    });
    var busy = status === "loading";
    $result.attr("aria-busy", busy ? "true" : "false");
    $form.find("input, textarea").prop("disabled", busy);
    $submit.prop("disabled", busy).toggleClass("is-loading", busy);
    $submit.find(".ds-btn__label").text(busy ? "Generating…" : (status === "success" ? "Generate new brief" : "Generate brief"));
    $("#regenerate-btn, #copy-btn").prop("disabled", busy);
  }

  // ---------------------------------------------------------------- form
  function readForm() {
    return {
      brand_name: $.trim($("#brand_name").val()),
      platform: $form.find("input[name=platform]:checked").val() || "",
      goal: $form.find("input[name=goal]:checked").val() || "",
      tone: $form.find("input[name=tone]:checked").val() || "",
      product_note: $.trim($("#product_note").val())
    };
  }

  function clearErrors() {
    FIELDS.forEach(function (name) { setFieldError(name, ""); });
  }

  function setFieldError(name, message) {
    var $field = $form.find('[data-field="' + name + '"]');
    $field.find(".ds-form-error").text(message).prop("hidden", !message);
    $field.toggleClass("fieldset-invalid", !!message);
    $field.find(".ds-input, .ds-textarea").attr("aria-invalid", message ? "true" : "false");
    if ($field.is("fieldset")) { $field.attr("aria-invalid", message ? "true" : "false"); }
  }

  function showFieldErrors(errors) {
    var first = null;
    FIELDS.forEach(function (name) {
      if (errors[name]) {
        setFieldError(name, [].concat(errors[name])[0]);
        first = first || name;
      }
    });
    if (first) {
      var $target = $form.find('[data-field="' + first + '"]').find("input, textarea").first();
      var $checked = $form.find('input[name="' + first + '"]:checked');
      ($checked.length ? $checked : $target).trigger("focus");
      announce("Please fix the highlighted fields.");
    }
  }

  function validate(payload) {
    var errors = {};
    Object.keys(CLIENT_ERRORS).forEach(function (name) {
      if (!payload[name]) { errors[name] = CLIENT_ERRORS[name]; }
    });
    if (payload.brand_name && payload.brand_name.length < 2) {
      errors.brand_name = "Brand name needs at least 2 characters.";
    }
    return errors;
  }

  // On stacked (mobile/tablet) layouts the result sits below the form: bring it into view.
  function revealResult() {
    if (!window.matchMedia("(max-width: 1023px)").matches) { return; }
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var top = $result.offset().top - $(".ds-nav-topbar").outerHeight() - 12;
    window.scrollTo({ top: Math.max(top, 0), behavior: reduce ? "auto" : "smooth" });
  }

  // ---------------------------------------------------------------- request
  function generate(payload) {
    if (state.pending) { return; } // block double submits
    var previous = state.status;
    state.lastPayload = payload;
    setState("loading");
    revealResult();
    announce("Generating your brief. This usually takes 10 to 20 seconds.");

    state.pending = $.ajax({ url: API_URL, method: "POST", data: JSON.stringify(payload), timeout: REQUEST_TIMEOUT_MS })
      .done(function (data) {
        renderBrief(data.brief, payload, data.meta || {});
        setState("success");
        announce("Your brief is ready. You can edit any text, then copy it.");
        var heading = document.getElementById("result-heading");
        heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
        revealResult();
      })
      .fail(function (xhr, textStatus) {
        var error = (xhr.responseJSON && xhr.responseJSON.error) || {};
        if (xhr.status === 400 && error.fields && Object.keys(error.fields).length) {
          setState(previous === "loading" ? "empty" : previous);
          showFieldErrors(error.fields);
          return;
        }
        var message = error.message;
        if (!message) {
          message = textStatus === "timeout"
            ? "This is taking longer than usual. Please try again."
            : "We couldn't reach the server. Check your connection and try again.";
        }
        $("#error-message").text(message);
        setState("error");
      })
      .always(function () { state.pending = null; });
  }

  // ---------------------------------------------------------------- render
  function editable(tag, text, key, label) {
    return $("<" + tag + ">")
      .addClass("editable")
      .attr({ contenteditable: EDIT_MODE, "data-key": key, "aria-label": label + " (editable)", spellcheck: "true" })
      .text(text);
  }

  function section(title, $content, extraClass) {
    var $section = $("<section>").addClass("brief-section " + (extraClass || ""));
    $section.append($("<h4>").addClass("brief-section__title").text(title), $content);
    return $section;
  }

  function list(items, key, label, variant, icon) {
    var $ul = $("<ul>").addClass("brief-list" + (variant ? " brief-list--" + variant : "")).attr("data-list", key);
    items.forEach(function (item, i) {
      var $li = $("<li>");
      if (icon) { $li.append(icon); }
      $li.append(editable("span", item, key, label + " " + (i + 1)));
      $ul.append($li);
    });
    return $ul;
  }

  function renderBrief(brief, payload, meta) {
    state.requestId = meta.request_id || null;
    state.edited = false;

    $("#brief-title").attr({ contenteditable: EDIT_MODE, "aria-label": "Campaign title (editable)" }).text(brief.campaign_title);
    $("#demo-badge").prop("hidden", meta.source !== "demo");

    var $tags = $("#brief-tags").empty();
    [LABELS.platform[payload.platform], LABELS.goal[payload.goal], LABELS.tone[payload.tone]].forEach(function (t) {
      $tags.append($("<li>").addClass("ds-tag").text(t));
    });

    var $body = $("#brief-body").empty();
    $body.append(section("Summary", editable("p", brief.summary, "summary", "Summary").addClass("brief-text")));
    $body.append(section("Objective", editable("p", brief.objective, "objective", "Objective").addClass("brief-text")));
    $body.append(section("Key message", $("<div>").addClass("highlight")
      .append(editable("p", brief.key_message, "key_message", "Key message"))));
    $body.append(section("Deliverables", list(brief.deliverables, "deliverables", "Deliverable")));

    var $cols = $("<div>").addClass("two-col");
    $cols.append(section("Do's", list(brief.dos, "dos", "Do", "dos", ICON_CHECK)));
    $cols.append(section("Don'ts", list(brief.donts, "donts", "Don't", "donts", ICON_X)));
    $body.append($cols);

    var $angles = $("<ol>").addClass("angle-grid");
    brief.content_angles.forEach(function (angle, i) {
      var n = i + 1;
      $angles.append($("<li>").addClass("angle").attr("data-angle", n).append(
        $("<span>").addClass("angle__num").text("Angle " + n),
        editable("p", angle.title, "angle_title", "Angle " + n + " title").addClass("angle__title"),
        editable("p", angle.hook, "angle_hook", "Angle " + n + " hook").addClass("angle__hook"),
        editable("p", angle.description, "angle_description", "Angle " + n + " description").addClass("angle__description")
      ));
    });
    $body.append(section("Content angles", $angles));

    var $criteria = $("<ul>").addClass("criteria");
    brief.creator_criteria.forEach(function (c, i) {
      $criteria.append($("<li>").append(
        editable("span", c.criterion, "criterion", "Criterion " + (i + 1)).addClass("criteria__name"),
        editable("span", c.detail, "criterion_detail", "Criterion " + (i + 1) + " detail").addClass("criteria__detail")
      ));
    });
    $body.append(section("Creator selection criteria", $criteria));
  }

  // ---------------------------------------------------------------- copy
  function textOf(el) {
    return $.trim((el.innerText || el.textContent || "").replace(/ /g, " "));
  }

  function briefAsText() {
    var p = state.lastPayload || {};
    var lines = [];
    var $root = $(".brief");
    function field(key) { return textOf($root.find('[data-key="' + key + '"]')[0]); }
    function bullets(key) {
      return $root.find('[data-list="' + key + '"] .editable').map(function () { return "- " + textOf(this); }).get();
    }

    lines.push(textOf(document.getElementById("brief-title")));
    lines.push([LABELS.platform[p.platform], LABELS.goal[p.goal], LABELS.tone[p.tone]].join(" · ") +
      (p.brand_name ? " · " + p.brand_name : ""));
    lines.push("", "SUMMARY", field("summary"));
    lines.push("", "OBJECTIVE", field("objective"));
    lines.push("", "KEY MESSAGE", field("key_message"));
    lines.push("", "DELIVERABLES"); lines = lines.concat(bullets("deliverables"));
    lines.push("", "DO'S"); lines = lines.concat(bullets("dos"));
    lines.push("", "DON'TS"); lines = lines.concat(bullets("donts"));
    lines.push("", "CONTENT ANGLES");
    $root.find(".angle").each(function (i) {
      var $a = $(this);
      lines.push((i + 1) + ". " + textOf($a.find('[data-key="angle_title"]')[0]));
      lines.push('   Hook: "' + textOf($a.find('[data-key="angle_hook"]')[0]) + '"');
      lines.push("   " + textOf($a.find('[data-key="angle_description"]')[0]));
    });
    lines.push("", "CREATOR SELECTION CRITERIA");
    $root.find(".criteria li").each(function () {
      var $c = $(this);
      lines.push("- " + textOf($c.find('[data-key="criterion"]')[0]) + ": " +
        textOf($c.find('[data-key="criterion_detail"]')[0]));
    });
    return lines.join("\n");
  }

  function legacyCopy(text) {
    var $tmp = $("<textarea>").val(text).attr("readonly", "").css({ position: "fixed", top: "-1000px", opacity: 0 });
    $("body").append($tmp);
    $tmp[0].select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    $tmp.remove();
    return ok;
  }

  function copyBrief() {
    var text = briefAsText();
    var done = function () {
      toast("Brief copied to clipboard");
      announce("Brief copied to clipboard.");
      track("brief_copied");
    };
    var fail = function () { toast("Couldn't copy automatically. Select the text and copy it manually.", true); };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { legacyCopy(text) ? done() : fail(); });
    } else if (legacyCopy(text)) {
      done();
    } else {
      fail();
    }
  }

  // ---------------------------------------------------------------- events
  $form.on("submit", function (e) {
    e.preventDefault();
    clearErrors();
    var payload = readForm();
    var errors = validate(payload);
    if (Object.keys(errors).length) {
      showFieldErrors(errors);
      return;
    }
    generate(payload);
  });

  $form.on("change input", "input, textarea", function () {
    var name = this.name;
    if ($form.find('[data-field="' + name + '"] .ds-form-error').text()) { setFieldError(name, ""); }
  });

  $("#product_note").on("input", function () {
    $("#product_note-count").text(this.value.length + "/280");
  });

  $("#retry-btn").on("click", function () {
    if (state.lastPayload) { generate(state.lastPayload); }
  });

  $("#regenerate-btn").on("click", function () {
    track("brief_regenerated");
    generate(readForm());
  });

  $("#copy-btn").on("click", copyBrief);

  $result.on("input", ".editable", function () {
    if (!state.edited) {
      state.edited = true;
      track("brief_edited");
    }
  });

  // Keep pasted content plain text in browsers without plaintext-only editing.
  $result.on("paste", ".editable", function (e) {
    if (EDIT_MODE === "plaintext-only") { return; }
    e.preventDefault();
    var text = (e.originalEvent.clipboardData || window.clipboardData).getData("text");
    document.execCommand("insertText", false, text);
  });

  // Enter in single-line fields (title, list items) finishes editing instead of adding a line.
  $result.on("keydown", "#brief-title, .brief-list .editable, .criteria .editable, .angle__title", function (e) {
    if (e.key === "Enter") { e.preventDefault(); this.blur(); }
  });

  setState("empty");
})(jQuery);
