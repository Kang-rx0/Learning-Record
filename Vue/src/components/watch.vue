<script setup lang="ts" name="watch">
import { ref, watch } from 'vue'

// ******************************* 监听 响应式 ***************************
const message = ref(0)

// 定义一个函数，用于记录 message 变化前后的值
function record(newValue: number, oldValue: number) {
  console.log(`message changed from ${oldValue} to ${newValue}`)
}
// 使用 watch 监听 message 的变化，并当发生变化时自动调用 record 函数
// 这里 record 就是回调函数
watch(message, record) 
const changeMsg = () => {
  message.value++
}
// ******************************* 监听 响应式 ***************************

// ******************************* 监听计算属性 ***************************
import {computed} from 'vue'
let count = ref(0)
let doubleCount = computed(() => count.value * 2)
function  changeCount(){
    count.value++
}
watch(doubleCount, (newCount, oldCount)=>{
    console.log(`doubleCount changed from ${oldCount} to ${newCount}`)
})
// ******************************* 监听计算属性 ***************************

// ******************************* 监听getter ***************************
let g_count = ref(0)
function changeGCount(){
    g_count.value++
}
watch(
    () => g_count.value*2, // 这一行就是getter函数（箭头函数）
    (newVal, oldVal) => {
        console.log(`g_count changed from ${oldVal} to ${newVal}`)
    }
)
// ******************************* 监听getter ***************************

</script>
<template>
  <p>{{ message }}</p>
  <button @click="changeMsg">更改 message</button>
  <button @click='changeCount'>更改 count</button>
  <button @click='changeGCount'>更改 g_count</button>
</template>