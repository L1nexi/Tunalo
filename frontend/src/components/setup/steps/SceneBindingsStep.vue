<script setup lang="ts">
import { ChevronDownIcon, LightbulbIcon, TriangleAlertIcon } from "@lucide/vue";
import { computed, ref } from "vue";

import type {
  Locale,
  PlaylistScanResult,
  SceneCatalogItem,
  SceneId,
} from "@/api/profile";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Combobox,
  ComboboxAnchor,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
  ComboboxTrigger,
  ComboboxViewport,
} from "@/components/ui/combobox";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { FieldError, FieldLabel } from "@/components/ui/field";
import { cn } from "@/lib/utils";
import { COPY, SCENE_DESCRIPTIONS, SCENE_LABELS } from "@/setup/copy";
import type { ProfileDraft } from "@/setup/model";

type Scenes = ProfileDraft["scenes"];
type Playlist = PlaylistScanResult["playlists"][number];

interface SceneCard {
  sceneId: SceneId;
  label: string;
  description: string;
  enabled: boolean;
  bindingInvalid: boolean;
  bound: Playlist | undefined;
}

interface SceneGroup {
  id: "season" | "context" | "weather";
  title: string;
  cards: SceneCard[];
}

const props = defineProps<{
  locale: Locale;
  mode: "setup" | "settings";
  scenes: Scenes;
  rememberedScenes: Scenes;
  catalog: SceneCatalogItem[];
  playlists: PlaylistScanResult["playlists"];
  catalogError: string;
  valid: boolean;
  attempted: boolean;
  errors: string[];
}>();

const emit = defineEmits<{
  "update:scenes": [value: Scenes];
  rememberScene: [id: SceneId, playlist: string];
  retryCatalog: [];
  openWallpaper: [];
}>();

const copy = computed(() => COPY[props.locale]);
const supportedScenes = computed(
  () => new Set(props.catalog.map((scene) => scene.id)),
);
const availablePlaylists = computed(
  () => new Set(props.playlists.map((playlist) => playlist.name)),
);
const openPicker = ref<SceneId | null>(null);

function toSceneCard(sceneId: SceneId): SceneCard {
  const name = props.scenes[sceneId];
  return {
    sceneId,
    label: SCENE_LABELS[props.locale][sceneId],
    description: SCENE_DESCRIPTIONS[props.locale][sceneId],
    enabled: sceneId in props.scenes,
    bindingInvalid:
      sceneId in props.scenes && !availablePlaylists.value.has(name ?? ""),
    bound: name
      ? props.playlists.find((playlist) => playlist.name === name)
      : undefined,
  };
}

const sceneGroups = computed<SceneGroup[]>(() => {
  const catalog: Array<{
    id: SceneGroup["id"];
    title: string;
    sceneIds: SceneId[];
  }> = [
    {
      id: "season",
      title: copy.value.scenes.groups.season,
      sceneIds: ["spring", "summer", "autumn", "winter"],
    },
    {
      id: "context",
      title: copy.value.scenes.groups.context,
      sceneIds: ["day_work", "day_leisure", "night_work", "night_leisure"],
    },
    {
      id: "weather",
      title: copy.value.scenes.groups.weather,
      sceneIds: ["sunset", "rain"],
    },
  ];
  return catalog
    .map(({ id, title, sceneIds }) => ({
      id,
      title,
      cards: sceneIds
        .filter((sceneId) => supportedScenes.value.has(sceneId))
        .map(toSceneCard),
    }))
    .filter((group) => group.cards.length > 0);
});

function groupEnabledCount(group: SceneGroup): number {
  return group.cards.filter((card) => card.enabled).length;
}

function toggleScene(
  sceneId: SceneId,
  enabled: boolean | "indeterminate",
): void {
  const updated = { ...props.scenes };
  if (enabled === true) {
    updated[sceneId] ??= props.rememberedScenes[sceneId] ?? "";
  } else {
    if (updated[sceneId]) emit("rememberScene", sceneId, updated[sceneId]);
    delete updated[sceneId];
  }
  if (openPicker.value === sceneId) openPicker.value = null;
  emit("update:scenes", updated);
}

function setPlaylist(sceneId: SceneId, value: unknown): void {
  if (typeof value === "string") {
    emit("update:scenes", { ...props.scenes, [sceneId]: value });
  }
}

function cardClass(card: SceneCard): string {
  return cn(
    "flex min-w-0 flex-col gap-2 rounded-lg border p-3",
    !card.enabled && "opacity-60",
    props.attempted && card.bindingInvalid && "border-destructive",
  );
}
</script>

<template>
  <section class="flex flex-col gap-6">
    <Alert v-if="mode === 'setup' && copy.scenes.defaultHint">
      <LightbulbIcon />
      <AlertDescription>{{ copy.scenes.defaultHint }}</AlertDescription>
    </Alert>

    <Alert v-if="catalogError" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription>{{ catalogError }}</AlertDescription>
      <Button variant="outline" size="sm" @click="emit('retryCatalog')">{{
        copy.common.retry
      }}</Button>
    </Alert>

    <Alert v-if="playlists.length === 0" variant="destructive">
      <TriangleAlertIcon />
      <AlertDescription>{{ copy.scenes.unavailable }}</AlertDescription>
      <Button variant="outline" size="sm" @click="emit('openWallpaper')">{{
        copy.wallpaper.title
      }}</Button>
    </Alert>

    <p class="text-sm text-muted-foreground">
      {{ copy.scenes.matchExplanation }}
    </p>

    <Collapsible
      v-for="group in sceneGroups"
      :key="group.id"
      :default-open="true"
    >
      <CollapsibleTrigger as-child>
        <button
          type="button"
          class="group flex w-full items-center gap-2 rounded-md px-1 py-1 text-left outline-none focus-visible:ring-2 focus-visible:ring-ring/30 hover:bg-accent/50"
        >
          <ChevronDownIcon
            class="transition-transform group-data-[state=closed]:-rotate-90"
          />
          <span class="text-sm font-medium">{{ group.title }}</span>
          <span class="text-sm text-muted-foreground">{{
            copy.scenes.groupSummary(
              groupEnabledCount(group),
              group.cards.length,
            )
          }}</span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div class="grid grid-cols-1 gap-3 pt-2 md:grid-cols-2 xl:grid-cols-3">
          <div
            v-for="card in group.cards"
            :key="card.sceneId"
            :class="cardClass(card)"
            :data-disabled="card.enabled ? undefined : ''"
          >
            <div class="flex items-center justify-between gap-2">
              <FieldLabel :for="`scene-${card.sceneId}`" class="font-medium">
                {{ card.label }}
              </FieldLabel>
              <Checkbox
                :id="`scene-${card.sceneId}`"
                :model-value="card.enabled"
                :disabled="playlists.length === 0"
                @update:model-value="
                  (value) => toggleScene(card.sceneId, value)
                "
              />
            </div>
            <p class="text-sm text-muted-foreground">{{ card.description }}</p>

            <template v-if="card.enabled">
              <Combobox
                :open="openPicker === card.sceneId"
                :model-value="scenes[card.sceneId] ?? ''"
                :reset-search-term-on-blur="true"
                @update:open="
                  (open) => (openPicker = open ? card.sceneId : null)
                "
                @update:model-value="
                  (value) => setPlaylist(card.sceneId, value)
                "
              >
                <ComboboxAnchor as-child>
                  <ComboboxTrigger as-child>
                    <Button
                      variant="outline"
                      class="w-full justify-between font-normal"
                      :aria-label="`${card.label}: ${copy.scenes.playlist}`"
                      :aria-invalid="attempted && card.bindingInvalid"
                      :aria-describedby="
                        attempted && card.bindingInvalid
                          ? `scene-error-${card.sceneId}`
                          : undefined
                      "
                    >
                      <span class="min-w-0 truncate">{{
                        scenes[card.sceneId] || copy.scenes.choosePlaylist
                      }}</span>
                      <ChevronDownIcon class="opacity-50" />
                    </Button>
                  </ComboboxTrigger>
                </ComboboxAnchor>
                <ComboboxList>
                  <ComboboxInput
                    :placeholder="copy.scenes.searchPlaylist"
                    :display-value="() => ''"
                  />
                  <ComboboxEmpty>{{
                    copy.scenes.noPlaylistMatch
                  }}</ComboboxEmpty>
                  <ComboboxViewport>
                    <ComboboxItem
                      v-for="playlist in playlists"
                      :key="playlist.name"
                      :value="playlist.name"
                    >
                      {{ playlist.name }}
                    </ComboboxItem>
                  </ComboboxViewport>
                </ComboboxList>
              </Combobox>
              <p v-if="card.bound" class="text-xs text-muted-foreground">
                {{ copy.scenes.playlistCount(card.bound.item_count) }}
              </p>
              <FieldError
                v-if="attempted && card.bindingInvalid"
                :id="`scene-error-${card.sceneId}`"
                :errors="[
                  scenes[card.sceneId]
                    ? copy.scenes.unavailablePlaylist
                    : copy.scenes.bindingRequired,
                ]"
              />
            </template>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>

    <FieldError
      v-if="(attempted && !valid) || errors.length"
      :errors="[
        ...(attempted && !valid ? [copy.scenes.required] : []),
        ...errors,
      ]"
    />
  </section>
</template>
