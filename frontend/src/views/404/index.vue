<script setup lang="ts">

import router from "@/router.ts";

const backAction = () => {
  router.replace('/')
}
</script>

<template>
  <div class="not-found-wrapper">
    <a-result status="404" title="404" sub-title="Sorry, the page you visited does not exist.">
      <template #extra>
        <a-button @click="backAction" type="primary">Back Home</a-button>
      </template>
    </a-result>
  </div>
</template>

<style lang="scss" scoped>
  .not-found-wrapper {
    height: calc(100vh - 104px);
  }
</style>
