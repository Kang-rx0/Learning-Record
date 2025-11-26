<template>
    <div class = 'computed'>
        姓：<input type="text" v-model="firstName" /><br>
        名：<input type="text" v-model="lastName" /><br>
        全名：<span>{{ fullName }}</span><br></br>
        <button @click="changeFullName">名字改为 li-si</button>
    </div>
</template>

<script setup lang="ts" name="computed">
    import {ref,computed} from 'vue'

    let firstName = ref('zhang')
    let lastName = ref('san');
    // 计算属性: 只读取，不修改
    /* let fullName = computed(()=>{
        return firstName.value + '-' + lastName.value
    }) */

    // 计算属性: 既读取，也修改
    let fullName = computed({
        // 读取
        get(){
            return firstName.value + '-' + lastName.value
        },
        // 修改
        set(val:string){
            console.log('命名被修改',val)
            
        // 需要在后面加上 ?? ''，因为firstName和lastName是string
        // 不这样加的话会说string类型不能被undefined复制
        // 因为undefined确实不能赋值给string，会报错
        // 而ts推断出了val可能是undefined的情况，所以会标红提醒
        // 添加了 ?? '' 之后就不会报错了，意思是如果 ??左边值为null或者undefined
        // 则取??右边的值

            firstName.value = val.split('-')[0]??''   
            lastName.value = val.split('-')[1]??''
        }
    })
    function changeFullName(){
        fullName.value = 'li-si'  // 通过修改fullName来间接修改firstName和lastName
    }
</script>
