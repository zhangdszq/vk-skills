(function () {
  var STORAGE_KEY = "skillhub_current_user";
  var DEFAULT_NAME = "钉钉用户";
  var DEFAULT_ROLE = "Skill 创作者";
  var CREATOR_COLORS = [
    "linear-gradient(135deg,#F0984F,#E07A2F)",
    "linear-gradient(135deg,#6558C4,#4E43A8)",
    "linear-gradient(135deg,#2EB8D9,#1A9DC0)",
    "linear-gradient(135deg,#3AAF6E,#2D8F58)",
    "linear-gradient(135deg,#D97706,#B45309)"
  ];

  function safeParse(raw) {
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }

  function hashString(value) {
    var str = String(value || "");
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
      hash = (hash << 5) - hash + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }

  function pickColor(name) {
    return CREATOR_COLORS[hashString(name) % CREATOR_COLORS.length];
  }

  function getInitial(name) {
    var clean = String(name || DEFAULT_NAME).trim();
    return clean ? clean.charAt(0).toUpperCase() : DEFAULT_NAME.charAt(0);
  }

  function normalizeProfile(input) {
    if (!input || typeof input !== "object") return null;
    var displayName = String(input.displayName || input.name || DEFAULT_NAME).trim() || DEFAULT_NAME;
    var profile = {
      id: String(input.id || input.unionId || input.openId || displayName).trim(),
      displayName: displayName,
      role: String(input.role || DEFAULT_ROLE).trim() || DEFAULT_ROLE,
      source: String(input.source || "manual").trim() || "manual",
      creatorColor: String(input.creatorColor || pickColor(displayName)).trim() || pickColor(displayName),
      avatarText: String(input.avatarText || getInitial(displayName)).trim() || getInitial(displayName),
      email: String(input.email || "").trim(),
      dept: String(input.dept || "").trim(),
      loggedInAt: input.loggedInAt || new Date().toISOString()
    };
    return profile;
  }

  function saveCurrentUser(profile) {
    var normalized = normalizeProfile(profile);
    if (!normalized) return null;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
    } catch (e) {}
    return normalized;
  }

  function getCurrentUser() {
    try {
      return normalizeProfile(safeParse(window.localStorage.getItem(STORAGE_KEY)));
    } catch (e) {
      return null;
    }
  }

  function clearCurrentUser() {
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch (e) {}
  }

  window.SKILLHUB_USER = {
    storageKey: STORAGE_KEY,
    defaultName: DEFAULT_NAME,
    defaultRole: DEFAULT_ROLE,
    getCurrentUser: getCurrentUser,
    saveCurrentUser: saveCurrentUser,
    clearCurrentUser: clearCurrentUser,
    normalizeProfile: normalizeProfile,
    pickColor: pickColor,
    getInitial: getInitial
  };
})();
