self.__MIDDLEWARE_MATCHERS = [
  {
    "regexp": "^(?:\\/(_next\\/data\\/[^/]{1,}))?\\/published(?:\\/((?:[^\\/#\\?]+?)(?:\\/(?:[^\\/#\\?]+?))*))?(\\.json|\\.rsc|\\.segments\\/.+\\.segment\\.rsc)?[\\/#\\?]?$",
    "originalSource": "/published/:docId*"
  },
  {
    "regexp": "^(?:\\/(_next\\/data\\/[^/]{1,}))?\\/published_mobile(?:\\/((?:[^\\/#\\?]+?)(?:\\/(?:[^\\/#\\?]+?))*))?(\\.json|\\.rsc|\\.segments\\/.+\\.segment\\.rsc)?[\\/#\\?]?$",
    "originalSource": "/published_mobile/:docId*"
  }
];self.__MIDDLEWARE_MATCHERS_CB && self.__MIDDLEWARE_MATCHERS_CB()