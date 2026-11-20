(() => {
  "use strict";

  /*
   * Mixamo bulk animation downloader
   *
   * Supports:
   * - Individual animations
   * - Animation packs
   * - 96 results per page
   * - Pages 1 through 26
   * - Resume/checkpoint support
   * - Retry handling
   * - Firefox-compatible activation events
   * - Download modals with missing or varying export controls
   *
   * Recommended starting state:
   * - Animations tab
   * - 96 Per Page
   * - Page 1
   * - No search term
   *
   * Browser setup:
   * - Allow multiple automatic downloads from Mixamo
   * - Disable "Always ask where to save files"
   * - Prevent the computer from sleeping
   *
   * Console controls:
   *   mixamoDownloader.status()
   *   mixamoDownloader.stop()
   *   mixamoDownloader.listFailures()
   *   mixamoDownloader.clearProgress()
   *   mixamoDownloader.inspectModal()
   */

  const SETTINGS = {
    /*
     * Preferred export settings.
     *
     * Missing controls are logged and skipped rather than
     * treated as errors.
     */
    format: "FBX Binary",
    includeSkin: false,
    fps: 24,
    keyframeReduction: "none",
    inPlace: true,

    /*
     * Catalog range.
     */
    startPage: 1,
    endPage: 1,

    /*
     * null downloads every item.
     * Set to 3 for a short test.
     */
    maxItemsPerPage: 3,

    /*
     * Timeouts.
     */
    selectionTimeoutMs: 30000,
    modalTimeoutMs: 20000,
    pageTimeoutMs: 30000,

    /*
     * Delays.
     */
    beforeCardClickDelayMs: 700,
    afterCardClickDelayMs: 1200,
    afterSelectionDelayMs: 1500,
    afterOptionChangeDelayMs: 600,
    afterDownloadClickDelayMs: 9000,
    packDownloadDelayMs: 18000,
    afterPageChangeDelayMs: 4000,
    retryDelayMs: 3500,

    /*
     * Additional attempts after the initial attempt.
     */
    retries: 2,

    /*
     * Save progress in localStorage.
     */
    resume: true,

    /*
     * Continue when an item fails all attempts.
     */
    skipFailedItems: true,
  };

  const STORAGE_KEY = "mixamo-library-downloader-v5";

  const state = {
    running: false,
    stopped: false,

    currentPage: SETTINGS.startPage,
    currentItem: 0,

    completedIds: new Set(),
    failures: [],
  };

  /*
   * General helpers
   */

  const wait = (milliseconds) =>
    new Promise((resolve) => {
      window.setTimeout(resolve, milliseconds);
    });

  function normalizeText(value) {
    return String(value ?? "")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function isElementVisible(element) {
    if (!element) {
      return false;
    }

    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();

    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      style.opacity !== "0" &&
      rect.width > 0 &&
      rect.height > 0
    );
  }

  async function waitForCondition(
    condition,
    {
      timeoutMs = 10000,
      intervalMs = 200,
      description = "condition",
    } = {},
  ) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      if (state.stopped) {
        throw new Error("Downloader stopped.");
      }

      try {
        const result = condition();

        if (result) {
          return result;
        }
      } catch {
        /*
         * Ignore temporary query failures while React rerenders.
         */
      }

      await wait(intervalMs);
    }

    throw new Error(
      `Timed out waiting for ${description}.`,
    );
  }

  /*
   * Saved progress
   */

  function loadState() {
    if (!SETTINGS.resume) {
      return;
    }

    try {
      const raw = localStorage.getItem(STORAGE_KEY);

      if (!raw) {
        return;
      }

      const saved = JSON.parse(raw);

      if (
        Number.isInteger(saved.currentPage) &&
        saved.currentPage >= SETTINGS.startPage &&
        saved.currentPage <= SETTINGS.endPage
      ) {
        state.currentPage = saved.currentPage;
      }

      if (
        Number.isInteger(saved.currentItem) &&
        saved.currentItem >= 0
      ) {
        state.currentItem = saved.currentItem;
      }

      state.completedIds = new Set(
        Array.isArray(saved.completedIds)
          ? saved.completedIds
          : [],
      );

      state.failures = Array.isArray(saved.failures)
        ? saved.failures
        : [];

      console.info("Restored Mixamo progress:", {
        page: state.currentPage,
        item: state.currentItem,
        completed: state.completedIds.size,
        failures: state.failures.length,
      });
    } catch (error) {
      console.warn(
        "Could not restore saved Mixamo progress:",
        error,
      );
    }
  }

  function saveState() {
    if (!SETTINGS.resume) {
      return;
    }

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        currentPage: state.currentPage,
        currentItem: state.currentItem,
        completedIds: [...state.completedIds],
        failures: state.failures,
        savedAt: new Date().toISOString(),
      }),
    );
  }

  function clearProgress() {
    localStorage.removeItem(STORAGE_KEY);

    state.currentPage = SETTINGS.startPage;
    state.currentItem = 0;
    state.completedIds.clear();
    state.failures = [];

    console.info("Saved Mixamo progress cleared.");
  }

  /*
   * Catalog card queries
   */

  function getDownloadableCards() {
    return [
      ...document.querySelectorAll(
        [
          ".product-results-holder .product-list .product-animation",
          ".product-results-holder .product-list .product-animation-pack",
        ].join(", "),
      ),
    ];
  }

  function getCardInfo(card, index) {
    const image = card.querySelector(
      ".product-image img",
    );

    const name =
      card
        .querySelector(".product-info p")
        ?.textContent?.trim() ||
      `Mixamo Item ${index + 1}`;

    const description =
      card
        .querySelector(".product-metadata li")
        ?.textContent?.trim() || "";

    const thumbnailUrl = image?.src || "";

    const isPack = card.classList.contains(
      "product-animation-pack",
    );

    const motionMatch = thumbnailUrl.match(
      /\/motions\/([^/]+)\/animated\.(?:gif|png|jpg|jpeg)/i,
    );

    const packMatch = thumbnailUrl.match(
      /\/motion_packs\/([^/]+)\/animated\.(?:gif|png|jpg|jpeg)/i,
    );

    const animationCount = isPack
      ? Number.parseInt(
          card
            .querySelector(".product-count")
            ?.textContent?.trim() || "",
          10,
        ) || null
      : 1;

    let itemId;

    if (isPack) {
      itemId =
        `pack:${packMatch?.[1] || normalizeText(name)}`;
    } else if (motionMatch?.[1]) {
      itemId = `motion:${motionMatch[1]}`;
    } else if (thumbnailUrl) {
      itemId = `motion-url:${thumbnailUrl}`;
    } else {
      itemId =
        `item:${state.currentPage}:${index}:${normalizeText(name)}`;
    }

    return {
      card,
      index,
      itemId,
      isPack,
      animationCount,
      name,
      description,
      thumbnailUrl,
    };
  }

  function findLiveItemById(itemId) {
    const cards = getDownloadableCards();

    for (
      let index = 0;
      index < cards.length;
      index += 1
    ) {
      const candidate = getCardInfo(
        cards[index],
        index,
      );

      if (candidate.itemId === itemId) {
        return candidate;
      }
    }

    return null;
  }

  /*
   * Pagination
   */

  function getCurrentPage() {
    const active = document.querySelector(
      ".pagination-holder .pagination li.active a",
    );

    const page = Number.parseInt(
      active?.textContent?.trim() || "",
      10,
    );

    return Number.isFinite(page)
      ? page
      : null;
  }

  function getNextPageButton() {
    const icon = document.querySelector(
      ".pagination-holder .pagination .fa-angle-right",
    );

    return icon?.closest("a") || null;
  }

  function hasNextPage() {
    const button = getNextPageButton();

    if (!button) {
      return false;
    }

    const listItem = button.closest("li");

    return !(
      listItem?.classList.contains("disabled") ||
      button.getAttribute("aria-disabled") === "true"
    );
  }

  function getCatalogSignature() {
    const cards = getDownloadableCards();

    return {
      page: getCurrentPage(),
      count: cards.length,

      firstImage:
        cards[0]
          ?.querySelector(".product-image img")
          ?.src || "",

      lastImage:
        cards[cards.length - 1]
          ?.querySelector(".product-image img")
          ?.src || "",
    };
  }

  async function goToNextPage() {
    const previous = getCatalogSignature();
    const nextButton = getNextPageButton();

    if (!nextButton || !hasNextPage()) {
      return false;
    }

    dispatchActivationEvents(nextButton);

    await waitForCondition(
      () => {
        const current = getCatalogSignature();

        return (
          current.count > 0 &&
          (
            current.page !== previous.page ||
            current.firstImage !== previous.firstImage ||
            current.lastImage !== previous.lastImage
          )
        );
      },
      {
        timeoutMs: SETTINGS.pageTimeoutMs,
        description: "the next catalog page",
      },
    );

    await wait(
      SETTINGS.afterPageChangeDelayMs,
    );

    return true;
  }

  async function goToPage(targetPage) {
    let currentPage = getCurrentPage();

    if (currentPage === null) {
      throw new Error(
        "Could not determine the current Mixamo page.",
      );
    }

    if (currentPage > targetPage) {
      throw new Error(
        `Mixamo is currently on page ${currentPage}, ` +
          `but saved progress expects page ${targetPage}. ` +
          `Open page ${targetPage} manually or clear progress.`,
      );
    }

    while (currentPage < targetPage) {
      const moved = await goToNextPage();

      if (!moved) {
        throw new Error(
          `Could not navigate from page ${currentPage} ` +
            `to page ${targetPage}.`,
        );
      }

      currentPage = getCurrentPage();

      if (currentPage === null) {
        throw new Error(
          "Lost the current page number while navigating.",
        );
      }
    }
  }

  /*
   * Preview queries
   */

  function getSelectedItemName() {
    return (
      document
        .querySelector(
          ".product-preview-holder .product-nav h2",
        )
        ?.textContent?.trim() || ""
    );
  }

  function getMainDownloadButton() {
    const buttons = [
      ...document.querySelectorAll(
        ".product-preview-holder .editor-sidebar .sidebar-header button",
      ),
    ];

    return (
      buttons.find(
        (button) =>
          normalizeText(button.textContent) ===
          "download",
      ) || null
    );
  }

  function getInPlaceCheckbox() {
    return document.querySelector(
      'input[name="inplace"]',
    );
  }

  /*
   * Firefox-compatible activation
   */

  function dispatchActivationEvents(element) {
    if (!element) {
      return;
    }

    const rect = element.getBoundingClientRect();

    const clientX = Math.round(
      rect.left + rect.width / 2,
    );

    const clientY = Math.round(
      rect.top + rect.height / 2,
    );

    const common = {
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
      button: 0,
      clientX,
      clientY,
    };

    const events = [
      [
        "pointerover",
        {
          ...common,
          buttons: 0,
          pointerType: "mouse",
          isPrimary: true,
        },
      ],
      [
        "mouseover",
        {
          ...common,
          buttons: 0,
        },
      ],
      [
        "pointerenter",
        {
          ...common,
          buttons: 0,
          pointerType: "mouse",
          isPrimary: true,
        },
      ],
      [
        "mouseenter",
        {
          ...common,
          buttons: 0,
        },
      ],
      [
        "pointerdown",
        {
          ...common,
          buttons: 1,
          pointerType: "mouse",
          isPrimary: true,
        },
      ],
      [
        "mousedown",
        {
          ...common,
          buttons: 1,
        },
      ],
      [
        "pointerup",
        {
          ...common,
          buttons: 0,
          pointerType: "mouse",
          isPrimary: true,
        },
      ],
      [
        "mouseup",
        {
          ...common,
          buttons: 0,
        },
      ],
      [
        "click",
        {
          ...common,
          buttons: 0,
        },
      ],
    ];

    for (const [type, options] of events) {
      try {
        const EventClass =
          type.startsWith("pointer")
            ? PointerEvent
            : MouseEvent;

        element.dispatchEvent(
          new EventClass(type, options),
        );
      } catch {
        try {
          element.dispatchEvent(
            new MouseEvent(type, options),
          );
        } catch {
          element.dispatchEvent(
            new Event(type, {
              bubbles: true,
              cancelable: true,
            }),
          );
        }
      }
    }

    try {
      element.click();
    } catch {
      // Native click is only a fallback.
    }
  }

  async function selectCatalogItem(item) {
    const liveItem =
      findLiveItemById(item.itemId);

    if (!liveItem) {
      throw new Error(
        `Could not re-find "${item.name}" in the current catalog.`,
      );
    }

    const card = liveItem.card;

    const clickTargets = [
      card.querySelector(".product-image"),
      card.querySelector(".product-overlay"),
      card.querySelector(".product-description"),
      card,
    ].filter(Boolean);

    card.scrollIntoView({
      behavior: "auto",
      block: "center",
      inline: "nearest",
    });

    await wait(
      SETTINGS.beforeCardClickDelayMs,
    );

    const previousName = getSelectedItemName();
    const previousNormalized =
      normalizeText(previousName);

    const expectedNormalized =
      normalizeText(item.name);

    for (const clickTarget of clickTargets) {
      dispatchActivationEvents(clickTarget);
      await wait(350);

      const currentNormalized =
        normalizeText(getSelectedItemName());

      if (
        currentNormalized &&
        currentNormalized !== previousNormalized
      ) {
        break;
      }
    }

    await wait(
      SETTINGS.afterCardClickDelayMs,
    );

    await waitForCondition(
      () => {
        const currentName =
          getSelectedItemName();

        const currentNormalized =
          normalizeText(currentName);

        if (
          !currentNormalized ||
          currentNormalized === "default character"
        ) {
          return false;
        }

        const exactMatch =
          currentNormalized === expectedNormalized;

        const partialMatch =
          currentNormalized.includes(expectedNormalized) ||
          expectedNormalized.includes(currentNormalized);

        const changed =
          currentNormalized !== previousNormalized;

        return (
          Boolean(getMainDownloadButton()) &&
          (
            exactMatch ||
            partialMatch ||
            changed
          )
        );
      },
      {
        timeoutMs:
          SETTINGS.selectionTimeoutMs,

        description:
          `"${item.name}" to load in the preview`,
      },
    );

    await wait(
      SETTINGS.afterSelectionDelayMs,
    );
  }

  /*
   * In Place option
   */

  async function setCheckboxState(
    checkbox,
    desiredState,
  ) {
    if (!checkbox) {
      return false;
    }

    if (checkbox.checked !== desiredState) {
      dispatchActivationEvents(checkbox);

      await waitForCondition(
        () =>
          checkbox.checked === desiredState,
        {
          timeoutMs: 4000,
          description:
            `In Place checkbox to become ${desiredState}`,
        },
      );
    }

    return checkbox.checked === desiredState;
  }

  /*
   * Download modal
   */

  function getVisibleDownloadModal() {
    const candidates = [
      ...document.querySelectorAll(
        [
          ".static-modal .modal",
          ".modal.in",
          ".modal[role='dialog']",
          ".static-modal",
        ].join(", "),
      ),
    ];

    return (
      candidates.find((modal) => {
        if (!isElementVisible(modal)) {
          return false;
        }

        return Boolean(
          modal.querySelector(
            "select, .modal-footer, button",
          ),
        );
      }) || null
    );
  }

  function inspectModal(modal = getVisibleDownloadModal()) {
    if (!modal) {
      console.warn(
        "No visible Mixamo download modal was found.",
      );

      return null;
    }

    const selects = [
      ...modal.querySelectorAll("select"),
    ].map((select, index) => ({
      index,
      name: select.name || "",
      id: select.id || "",
      className: select.className || "",
      value: select.value,
      options: [...select.options].map(
        (option) => ({
          text: option.textContent.trim(),
          value: option.value,
          selected: option.selected,
        }),
      ),
    }));

    const buttons = [
      ...modal.querySelectorAll("button, .btn"),
    ].map((button, index) => ({
      index,
      text: button.textContent.trim(),
      className: button.className || "",
      disabled: button.disabled,
    }));

    const result = {
      text: modal.textContent
        .replace(/\s+/g, " ")
        .trim(),
      selects,
      buttons,
    };

    console.log(
      "Mixamo modal inspection:",
      result,
    );

    console.table(
      selects.map((select) => ({
        index: select.index,
        id: select.id,
        name: select.name,
        value: select.value,
        options: select.options
          .map((option) => option.text)
          .join(" | "),
      })),
    );

    return result;
  }

  function findSelectContainingOptions(
    modal,
    optionTexts,
  ) {
    const wanted =
      optionTexts.map(normalizeText);

    return (
      [...modal.querySelectorAll("select")].find(
        (select) => {
          const available = [
            ...select.options,
          ].map((option) =>
            normalizeText(
              option.textContent,
            ),
          );

          return wanted.some(
            (wantedText) =>
              available.some(
                (availableText) =>
                  availableText.includes(
                    wantedText,
                  ),
              ),
          );
        },
      ) || null
    );
  }

  async function selectOptionByText(
    select,
    desiredTexts,
    {
      settingName = "option",
    } = {},
  ) {
    if (!select) {
      console.info(
        `${settingName}: control not available; keeping Mixamo's current setting.`,
      );

      return false;
    }

    const desired =
      desiredTexts.map(normalizeText);

    const matchingOption = [
      ...select.options,
    ].find((option) => {
      const optionText = normalizeText(
        option.textContent,
      );

      return desired.some(
        (desiredText) =>
          optionText === desiredText ||
          optionText.includes(desiredText) ||
          desiredText.includes(optionText),
      );
    });

    if (!matchingOption) {
      const availableOptions = [
        ...select.options,
      ]
        .map((option) =>
          option.textContent.trim(),
        )
        .join(", ");

      console.warn(
        `${settingName}: requested option not available. ` +
          `Keeping current value. Available options: ${availableOptions}`,
      );

      return false;
    }

    if (
      select.value !== matchingOption.value
    ) {
      select.value =
        matchingOption.value;

      select.dispatchEvent(
        new Event("input", {
          bubbles: true,
        }),
      );

      select.dispatchEvent(
        new Event("change", {
          bubbles: true,
        }),
      );

      await wait(
        SETTINGS.afterOptionChangeDelayMs,
      );
    }

    console.info(
      `${settingName}: ` +
        matchingOption.textContent.trim(),
    );

    return true;
  }

  async function configureDownloadModal(
    modal,
    item,
  ) {
    /*
     * Log the controls once for diagnostic purposes.
     */
    const selects = [
      ...modal.querySelectorAll("select"),
    ];

    console.info(
      `"${item.name}" download modal contains ${selects.length} select control(s).`,
    );

    const formatSelect =
      findSelectContainingOptions(
        modal,
        [
          "fbx binary",
          "fbx",
          "collada",
          "dae",
        ],
      );

    await selectOptionByText(
      formatSelect,
      [SETTINGS.format],
      {
        settingName: "Format",
      },
    );

    const skinSelect =
      findSelectContainingOptions(
        modal,
        [
          "with skin",
          "without skin",
        ],
      );

    await selectOptionByText(
      skinSelect,
      SETTINGS.includeSkin
        ? ["With Skin"]
        : ["Without Skin"],
      {
        settingName: "Skin",
      },
    );

    const fpsSelect =
      findSelectContainingOptions(
        modal,
        [
          "24 fps",
          "30 fps",
          "60 fps",
          "frames per second",
        ],
      );

    await selectOptionByText(
      fpsSelect,
      [
        `${SETTINGS.fps} FPS`,
        String(SETTINGS.fps),
      ],
      {
        settingName: "Frames per Second",
      },
    );

    const reductionSelect =
      findSelectContainingOptions(
        modal,
        [
          "no keyframe reduction",
          "keyframe reduction",
          "uniform",
          "non-uniform",
          "non uniform",
          "none",
        ],
      );

    const reductionOptions = {
      none: [
        "None",
        "No Keyframe Reduction",
      ],

      uniform: [
        "Uniform",
      ],

      "non-uniform": [
        "Non-uniform",
        "Non Uniform",
      ],
    };

    await selectOptionByText(
      reductionSelect,
      reductionOptions[
        SETTINGS.keyframeReduction
      ] || ["None"],
      {
        settingName:
          "Keyframe Reduction",
      },
    );
  }

  function getModalDownloadButton(modal) {
    const buttons = [
      ...modal.querySelectorAll(
        "button, .btn",
      ),
    ].filter(isElementVisible);

    return (
      buttons.find((button) => {
        const text = normalizeText(
          button.textContent,
        );

        return (
          text === "download" ||
          text.includes("download")
        );
      }) ||
      modal.querySelector(
        ".modal-footer .btn-primary",
      ) ||
      null
    );
  }

  async function openDownloadModal() {
    const mainButton =
      await waitForCondition(
        () => getMainDownloadButton(),
        {
          timeoutMs:
            SETTINGS.modalTimeoutMs,
          description:
            "the main preview Download button",
        },
      );

    dispatchActivationEvents(
      mainButton,
    );

    return await waitForCondition(
      () => getVisibleDownloadModal(),
      {
        timeoutMs:
          SETTINGS.modalTimeoutMs,

        description:
          "the Mixamo download modal",
      },
    );
  }

  async function waitForModalToClose(
    modal,
  ) {
    try {
      await waitForCondition(
        () =>
          !document.contains(modal) ||
          !isElementVisible(modal),
        {
          timeoutMs: 12000,
          description:
            "the download modal to close",
        },
      );
    } catch {
      console.info(
        "Modal-close confirmation timed out; continuing after the download delay.",
      );
    }
  }

  /*
   * Download processing
   */

  async function downloadItem(item) {
    await selectCatalogItem(item);

    const inPlaceCheckbox =
      getInPlaceCheckbox();

    if (inPlaceCheckbox) {
      await setCheckboxState(
        inPlaceCheckbox,
        SETTINGS.inPlace,
      );

      console.info(
        `In Place: ${SETTINGS.inPlace}`,
      );
    } else {
      console.info(
        `"${item.name}" has no In Place option.`,
      );
    }

    const modal =
      await openDownloadModal();

    await configureDownloadModal(
      modal,
      item,
    );

    const finalDownloadButton =
      getModalDownloadButton(modal);

    if (!finalDownloadButton) {
      inspectModal(modal);

      throw new Error(
        `Could not find the final Download button for "${item.name}".`,
      );
    }

    dispatchActivationEvents(
      finalDownloadButton,
    );

    await waitForModalToClose(modal);

    await wait(
      item.isPack
        ? SETTINGS.packDownloadDelayMs
        : SETTINGS.afterDownloadClickDelayMs,
    );
  }

  function recordFailure(item, error) {
    state.failures =
      state.failures.filter(
        (failure) =>
          failure.itemId !== item.itemId,
      );

    state.failures.push({
      page: state.currentPage,
      index: item.index,
      itemId: item.itemId,
      name: item.name,

      type: item.isPack
        ? "animation-pack"
        : "animation",

      error: String(
        error?.message || error,
      ),

      failedAt:
        new Date().toISOString(),
    });

    saveState();
  }

  async function processItem(item) {
    if (
      state.completedIds.has(
        item.itemId,
      )
    ) {
      console.info(
        `Skipping completed ${
          item.isPack
            ? "pack"
            : "animation"
        }: ${item.name}`,
      );

      return true;
    }

    const totalAttempts =
      SETTINGS.retries + 1;

    for (
      let attempt = 1;
      attempt <= totalAttempts;
      attempt += 1
    ) {
      if (state.stopped) {
        throw new Error(
          "Downloader stopped.",
        );
      }

      console.group(
        `Page ${state.currentPage}, ` +
          `item ${item.index + 1}: ` +
          item.name,
      );

      console.info({
        type: item.isPack
          ? "animation pack"
          : "animation",

        itemId: item.itemId,

        animationCount:
          item.animationCount,

        description:
          item.description,

        attempt,
        totalAttempts,
      });

      try {
        await downloadItem(item);

        state.completedIds.add(
          item.itemId,
        );

        state.failures =
          state.failures.filter(
            (failure) =>
              failure.itemId !==
              item.itemId,
          );

        saveState();

        console.info(
          `Completed "${item.name}". ` +
            `Total completed files: ` +
            state.completedIds.size,
        );

        console.groupEnd();

        return true;
      } catch (error) {
        console.error(
          `Attempt ${attempt} failed:`,
          error,
        );

        console.groupEnd();

        if (
          attempt < totalAttempts
        ) {
          await wait(
            SETTINGS.retryDelayMs,
          );
        } else {
          recordFailure(
            item,
            error,
          );
        }
      }
    }

    return false;
  }

  /*
   * Public controls
   */

  window.mixamoDownloader = {
    stop() {
      state.stopped = true;
      saveState();

      console.warn(
        "The downloader will stop after the current operation.",
      );
    },

    status() {
      return {
        running: state.running,
        stopped: state.stopped,
        currentPage:
          state.currentPage,
        currentItem:
          state.currentItem,
        completedFiles:
          state.completedIds.size,
        failures: [
          ...state.failures,
        ],
        settings: {
          ...SETTINGS,
        },
      };
    },

    listFailures() {
      console.table(
        state.failures,
      );

      return [
        ...state.failures,
      ];
    },

    inspectModal() {
      return inspectModal();
    },

    clearProgress,
  };

  /*
   * Main loop
   */

  async function start() {
    if (state.running) {
      console.warn(
        "The Mixamo downloader is already running.",
      );

      return;
    }

    state.running = true;
    state.stopped = false;

    loadState();

    console.info(
      "Starting Mixamo downloader.",
      SETTINGS,
    );

    console.info(
      "Available controls:",
      {
        status:
          "mixamoDownloader.status()",

        stop:
          "mixamoDownloader.stop()",

        failures:
          "mixamoDownloader.listFailures()",

        inspectModal:
          "mixamoDownloader.inspectModal()",

        clear:
          "mixamoDownloader.clearProgress()",
      },
    );

    try {
      await goToPage(
        Math.max(
          SETTINGS.startPage,
          state.currentPage,
        ),
      );

      while (
        !state.stopped &&
        state.currentPage >= SETTINGS.startPage &&
        state.currentPage <= SETTINGS.endPage
      ) {
        const visiblePage =
          getCurrentPage();

        if (visiblePage !== null) {
          state.currentPage =
            visiblePage;
        }

        const initialCards =
          getDownloadableCards();

        if (
          initialCards.length === 0
        ) {
          throw new Error(
            `No downloadable items found on page ${state.currentPage}.`,
          );
        }

        const pageItemLimit =
          SETTINGS.maxItemsPerPage === null
            ? initialCards.length
            : Math.min(
                initialCards.length,
                SETTINGS.maxItemsPerPage,
              );

        console.info(
          `Page ${state.currentPage}: ` +
            `${initialCards.length} downloadable items found; ` +
            `${pageItemLimit} will be processed.`,
        );

        const startingIndex =
          Math.min(
            state.currentItem,
            pageItemLimit,
          );

        for (
          let index = startingIndex;
          index < pageItemLimit;
          index += 1
        ) {
          if (state.stopped) {
            break;
          }

          const freshCards =
            getDownloadableCards();

          const card =
            freshCards[index];

          if (!card) {
            console.error(
              `Item ${index + 1} disappeared after a React rerender.`,
            );

            state.currentItem =
              index + 1;

            saveState();
            continue;
          }

          state.currentItem = index;
          saveState();

          const item =
            getCardInfo(
              card,
              index,
            );

          const succeeded =
            await processItem(item);

          if (
            !succeeded &&
            !SETTINGS.skipFailedItems
          ) {
            throw new Error(
              `"${item.name}" failed and skipFailedItems is false.`,
            );
          }

          state.currentItem =
            index + 1;

          saveState();
        }

        if (state.stopped) {
          break;
        }

        state.currentItem = 0;
        saveState();

        if (
          state.currentPage >= SETTINGS.endPage ||
          !hasNextPage()
        ) {
          break;
        }

        const moved =
          await goToNextPage();

        if (!moved) {
          break;
        }

        state.currentPage =
          getCurrentPage() ||
          state.currentPage + 1;

        state.currentItem = 0;

        saveState();
      }

      if (state.stopped) {
        console.warn(
          "Downloader stopped. Progress was saved.",
        );

        return;
      }

      console.info(
        "Mixamo download pass finished.",
        {
          completedFiles:
            state.completedIds.size,

          failedFiles:
            state.failures.length,

          failures:
            state.failures,
        },
      );

      alert(
        [
          "Mixamo download pass finished.",
          "",
          `Completed files: ${state.completedIds.size}`,
          `Failed files: ${state.failures.length}`,
          "",
          "Check the browser download list and console.",
        ].join("\n"),
      );
    } catch (error) {
      saveState();

      console.error(
        "Mixamo downloader stopped with an error:",
        error,
      );
    } finally {
      state.running = false;
    }
  }

  start();
})();