<template>
    <div class = Person>
        <h1>这是H1-显示名字</h1>
        <h2>名字：{{name}}</h2>
        <h2>年龄：{{age}}</h2>
        <button @click = "changeName">修改名字</button> 
        <button @click = "changeAge">修改年龄</button>
        <button @click = "showTele">显示电话</button>
    </div>      
</template>

<!-- 
这一节是关于响应式变量的，用 let var = ref(初始值) 来定义响应式变量，这样当变量的值被修改时，也能同步到网页上显示出来。 

这里ref返回的是 ref对象，ref对象的 值存储在它的 .value 属性中
因此当需要修改或者读取值时，需要通过 .value 来访问:
    name.value = 'Zhang San';

但是在模版中就可以直接用变量名调用：
    <h2>名字：{{name}}</h2>
-->
<script lang = "ts">
    export default {
        name: 'Person'
    }
</script>

<script setup lang = 'ts'>
    import { ref } from 'vue';

    let name = ref('张三');
    let age = ref(18);
    let tele = ref('12345678901');

    function changeName(){
        name.value = 'Zhang San';  // 例如这里用 .value 来修改name的值
    };                 

    function changeAge(){
        age.value +=1;  
    };

    function showTele(){
        alert(tele.value);   
    };

    return {name,age,changeName,changeAge,showTele};
</script>