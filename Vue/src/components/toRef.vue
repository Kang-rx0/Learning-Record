<template>
    <div class = 'toRef'>
        <h1> 使用toRef实现响应式数据</h1>
        <h2>Name: {{ person.name }}</h2>
        <h2>Age: {{ person.age }}</h2>
        <h2>Gender: {{ person.gender }}</h2>
        <button @click="changeName">修改名字</button>
        <button @click="changeAge">修改年龄</button>
        <button @click="changeGender">修改性别</button>
    </div>
</template>

<script setup lang="ts" name="toRef">

// toRef 用于将响应式对象的某个属性转换为ref，从而实现对该属性的响应式处理  
// toRefs 用于将响应式对象的所有属性转换为ref，批量实现响应式处理
import { ref,reactive, toRef, toRefs } from 'vue';
let person = reactive({
    name: '李四',
    age: 20,
    gender: '男'});

// 通过toRefs将person对象中的n个属性批量取出，且依然保持响应式的能力
let {name,gender} =  toRefs(person);

// 通过toRef将person对象中的age属性单独取出，且依然保持响应式的能力
let age = toRef(person,'age');

function changeName(){
    name.value = 'Li Si';  // 修改名字,因为是ref类型，所以要用.value
};
function changeAge(){
    age.value = 30;  // 修改年龄
};
function changeGender(){
    gender.value = '女';  // 修改性别
};
</script>