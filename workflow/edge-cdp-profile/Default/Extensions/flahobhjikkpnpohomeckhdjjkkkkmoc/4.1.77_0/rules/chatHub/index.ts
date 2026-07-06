import Browser from 'webextension-polyfill'

class DeclarativeNetRequestRuleIds {
  private static current_id = 100

  static getNextId() {
    return DeclarativeNetRequestRuleIds.current_id++
  }
}

const createRemoveXFrameOptionsRule = (
  urlFilter: string,
  tabId: number,
): Browser.DeclarativeNetRequest.Rule => {
  return {
    id: DeclarativeNetRequestRuleIds.getNextId(),
    priority: 1,
    action: {
      type: 'modifyHeaders',
      responseHeaders: [
        {
          header: 'content-security-policy',
          operation: 'remove',
        },
        {
          header: 'x-frame-options',
          operation: 'remove',
        },
      ],
    },
    condition: {
      urlFilter,
      isUrlFilterCaseSensitive: false,
      resourceTypes: ['sub_frame'],
      tabIds: [tabId],
    },
  }
}
    
export const createChatHubRule = (tabId: number): {
  rules: Browser.DeclarativeNetRequest.Rule[]
  ruleIds: number[]
} => {
  const rules = [
    // createRemoveXFrameOptionsRule('||google.com', tabId), // www.google.com / accounts.google.com / ogs.google.com 等
    // createRemoveXFrameOptionsRule('||perplexity.ai', tabId),
    // createRemoveXFrameOptionsRule('||chatgpt.com', tabId),
    // createRemoveXFrameOptionsRule('||openai.com', tabId),
    // createRemoveXFrameOptionsRule('||bing.com', tabId),
    // createRemoveXFrameOptionsRule('||baidu.com', tabId),

    createRemoveXFrameOptionsRule('*', tabId), // 移除所有页面的 X-Frame-Options 头，避免搜索结果点击后不能访问
  ]
  console.log('创建规则', rules)

  return {
    rules,
    ruleIds: rules.map((rule) => rule.id),
  }
}
