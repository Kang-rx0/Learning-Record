<script setup lang="ts">
import HelloWorld from './components/HelloWorld.vue'
import person from './components/forSetup.vue'
import mine from './components/mine.vue'
import item from './components/reactive.vue'  
import computed from './components/computed.vue'
import watch from './components/watch.vue'
</script>

<template>
  <div>
    <a href="https://vite.dev" target="_blank">
      <img src="/vite.svg" class="logo" alt="Vite logo" />
    </a>
    <a href="https://vuejs.org/" target="_blank">
      <img src="./assets/vue.svg" class="logo vue" alt="Vue logo" />
    </a>
  </div>
  <!-- <HelloWorld msg="Vite + Vue" /> -->

<!-- 
  下面这个div容器作用：将 mine 和 item 组件放在一个div容器，然后给容器加上flex布局
这样就能做到 mine 和 item 组件左右并排显示在页面上 
-->
  <div class="row-container">
    <mine />
    <item />
  </div>
  <div class="row-container">
    <computed />
    <person />
  </div>
  <watch />

</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}

.row-container {
  display: flex;
  flex-direction: row;
  gap: 32px;
  margin-top: 24px;
}
</style>
