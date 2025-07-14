<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <header>
    <div class="wrapper">
      <h1>AlphaHunter驾驶舱</h1>
      <nav>
        <!-- 未来可以在这里添加导航链接 -->
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 2rem;
}

.wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h1 {
  font-weight: 700;
  font-size: 1.5rem;
}
</style>
